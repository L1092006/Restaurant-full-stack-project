# Deploy — AWS Infrastructure as Code

CloudFormation templates and shell scripts that stand up the full restaurant
platform on AWS: a VPC, an Application Load Balancer in front of an Auto Scaling
Group of EC2 instances (Django API + chatbot), an RDS MySQL database, and an
S3 + CloudFront distribution for the React frontend.

> Part of the [Restaurant full-stack project](../README.md).
>
> **Origin:** the CloudFormation templates were initially AI-generated and then
> customized by hand. They target a demo/learning environment — see
> [Security notes](#security-notes) before considering production use.

## Layout

```
deploy/
├── README.md
├── cloud_formation_templates/
│   ├── vpc_dev.yaml          # Stack 1: VPC + networking
│   ├── backend_infra.yaml    # Stack 2: ALB, ASG/EC2, RDS, S3, CloudFront
│   └── .env                  # deploy parameters (not committed)
└── scripts/
    ├── deploy.sh             # deploy both stacks (VPC first, then app)
    ├── uploadS3.sh           # build frontend, sync to S3, invalidate CloudFront
    ├── deleteStacks.sh       # empty bucket + tear down both stacks
    └── .env                  # deploy parameters (not committed)
```

## Architecture

```
                    Internet
                       │
         ┌─────────────┴──────────────┐
         │                            │
   CloudFront (OAC)             Application Load Balancer  (HTTPS :443, HTTP→HTTPS)
         │                            │  path-based routing:
   S3 (private, SPA)                  │    /api/*        → :8000  (Django, health /api/items/)
                                      │    /chat, /chat/* → :8001 (chatbot, health /health)
                                      │    default        → :8000
                                      ▼
                        Auto Scaling Group (EC2, private subnets)
                                      │
                                      ▼
                            RDS MySQL 8.4 (private subnets)
```

Two stacks, coupled only through CloudFormation Exports:

- **`vpc_dev.yaml`** — VPC `10.1.0.0/16`, 2 AZs, public + private subnets, an
  Internet Gateway, and a single NAT Gateway. Exports `VPCId`, the two public and
  two private subnet ids.
- **`backend_infra.yaml`** — the application tier. Imports the VPC exports via
  its `NetworkStackName` parameter, which **must equal the VPC stack's name**.
  Creates:
  - Internet-facing **ALB** (HTTPS listener with ACM cert; HTTP→HTTPS redirect)
    with path rules for the API (`:8000`) and chatbot (`:8001`, sticky sessions).
  - **Launch Template + Auto Scaling Group** of Ubuntu EC2 instances in the
    private subnets (see [Self-provisioning](#self-provisioning)).
  - **RDS MySQL 8.4** (`db.t3.micro`, encrypted, 7-day backups) reachable only
    from the EC2 security group.
  - **S3 bucket** (private) + **CloudFront** distribution (OAC, SPA error
    routing: 403/404 → `/index.html`) for the frontend.

## Self-provisioning

Nothing is baked into an AMI or uploaded by the template. The launch template's
`UserData`:

1. Clones `github.com/L1092006/Restaurant-full-stack-project` and checks out the
   **`deploy_aws`** branch.
2. Creates a `backend_admin` user that owns the checkout.
3. Runs `backend/setup.sh` and `chatbot_backend/setup.sh`, which each create a
   virtualenv, write a `.env`, migrate, and install a systemd unit
   (`restaurantAPI.service` / `chatbot.service`).

> **Push your code to `deploy_aws` before launching new instances** — instances
> pull that branch at boot.

## Prerequisites

Provide these before deploying (they are not created by the templates):

- An **ACM certificate** for your domain, in **`us-east-1`** (used by both
  CloudFront and the ALB). This forces the whole deploy to `us-east-1`.
- An **IAM instance profile** for EC2 (SSM access recommended).
- A **globally-unique S3 bucket name** for the frontend.
- A **Route 53** hosted zone / domain for the CloudFront and ALB records.
- (Optional) an **EC2 key pair** — note the `KeyPairName` parameter exists but
  is not currently attached to the launch template, so there is no SSH key by
  default; use SSM via the instance profile instead.

## Deploying

Populate `deploy/scripts/.env` (sourced by the scripts) with at least:

```bash
ProjectName=restaurant
VPC_STACKNAME=n-stack-restaurant-vpc
BACKEND_STACKNAME=n-stack-restaurant-app
VPC_REGION=us-east-1
BACKEND_REGION=us-east-1
DBPassword=<min 8 chars>
BackendAdminUsername=<django admin user>
BackendAdminPassword=<django admin password>
DjangoKey=<django secret key>
PineconeKey=<pinecone api key>
OpenRouterKey=<openrouter api key>
S3BucketName=<globally-unique bucket>
CloudALias=<cloudfront domain alias>
KeyPairName=<ec2 key pair>
IAMInstanceProfile=<ec2 instance profile>
```

Then, from `deploy/`:

```bash
# 1. Deploy the VPC stack, wait, then the app stack (NetworkStackName = VPC stack name)
. scripts/deploy.sh

# 2. Point the frontend's VITE_BACKEND_URL / VITE_CHATBOT_URL at the new ALB,
#    then build and upload the SPA and invalidate CloudFront
. scripts/uploadS3.sh

# 3. In Route 53, update records to point at the new ALB / CloudFront distribution
# 4. In cloudfront, go to the new distribution and route it to the custom domain
```

`deploy.sh` deploys `vpc_dev.yaml` first, waits for
`stack-create-complete`, then deploys `backend_infra.yaml` with
`NetworkStackName` set to the VPC stack. No `--capabilities` flag is needed
(the templates create no IAM resources).

Equivalent manual commands:

```bash
cd deploy/cloud_formation_templates    # region MUST be us-east-1
aws cloudformation deploy --template-file vpc_dev.yaml \
  --stack-name n-stack-restaurant-vpc --region us-east-1

aws cloudformation deploy --template-file backend_infra.yaml \
  --stack-name n-stack-restaurant-app --region us-east-1 \
  --parameter-overrides NetworkStackName=n-stack-restaurant-vpc DBPassword=<min8> \
    BackendAdminUsername=<u> BackendAdminPassword=<p> DjangoKey=<secret> \
    PineconeKey=<k> OpenRouterKey=<k>
```

## Tearing down

```bash
. scripts/deleteStacks.sh    # empties the S3 bucket, deletes the app stack, then the VPC stack
```

Then delete the Route 53 records that pointed at the CloudFront distribution / ALB.

## Security notes

These templates are for a demo/learning deployment, not production:

- **Secrets are passed through EC2 `UserData`** to the setup scripts, and some
  are passed **unquoted** — a secret containing a space will word-split and
  corrupt the generated `.env`. Prefer AWS Secrets Manager / SSM Parameter Store
  for real deployments.
- `setup.sh` writes **`STAGE=PRE_PROD`**, so the Django app does not enable its
  production hardening (env-driven `ALLOWED_HOSTS`/CORS, proxy SSL header,
  gunicorn keepalive tuning) — those only activate at `STAGE=PROD`. Behind the
  ALB, gunicorn's keepalive stays at 5s (below the ALB's 60s idle timeout).
- `RDSInstance` uses `DeletionPolicy: Delete` (the database is destroyed on
  stack deletion) and `MultiAZ: false`.
- The frontend is **not** deployed by the stack; upload it separately with
  `scripts/uploadS3.sh`.
