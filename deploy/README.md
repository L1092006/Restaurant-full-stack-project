# Deploy — AWS Infrastructure as Code

CloudFormation templates and shell scripts that run the restaurant platform on
AWS: a VPC, a load balancer in front of an Auto Scaling group of EC2 servers
running the two backend containers, an RDS MySQL database, and S3 + CloudFront
for the React frontend.

> Part of the [Restaurant full-stack project](../README.md).
>
> **Origin:** the CloudFormation templates were initially AI-generated and then
> customized by hand. They target a demo/learning environment — see
> [Security notes](#security-notes) before considering production use.

**There are two ways to deploy:**

- **[Option A — automatic](#option-a-automatic-deploys-with-github-actions):**
  merge to `main`, and GitHub Actions tests, builds, and deploys everything.
  Use this normally.
- **[Option B — manual](#option-b-manual-deploys-from-your-machine):** run the
  scripts from your own computer.

Both need the [one-time prerequisites](#prerequisites-one-time) first.

## Contents

- [Layout](#layout)
- [Architecture](#architecture)
- [How a server starts](#how-a-server-starts)
- [Prerequisites (one-time)](#prerequisites-one-time)
- [Option A: Automatic deploys with GitHub Actions](#option-a-automatic-deploys-with-github-actions)
- [Option B: Manual deploys from your machine](#option-b-manual-deploys-from-your-machine)
- [Updating and rolling back](#updating-and-rolling-back)
- [Troubleshooting](#troubleshooting)
- [Tearing down](#tearing-down)
- [Minimal demo stack (older setup)](#minimal-demo-stack-older-setup)
- [Security notes](#security-notes)

## Layout

```
deploy/
├── README.md
├── cloud_formation_templates/
│   ├── vpc_dev.yaml           # Stack 1: VPC + networking
│   ├── backend_infra.yaml     # Stack 2: load balancer, Auto Scaling group, RDS, S3, CloudFront
│   ├── minimal_backend.yaml   # cheaper single-server demo stack (older setup, see below)
│   └── .env                   # your deploy settings — not committed (see Option B, step 1)
└── scripts/
    ├── deploy.sh              # create/update both stacks:  deploy.sh <image-tag>
    ├── uploadS3.sh            # build the frontend, upload it to S3, clear the CloudFront cache
    ├── deleteStacks.sh        # empty the bucket, delete both stacks
    ├── deploy_minimal.sh      # deploy the minimal demo stack
    ├── delete_minimal.sh      # delete the minimal demo stack
    └── compose.yaml           # run both containers on one machine, for testing
```

## Architecture

```
                    Internet
                       │
         ┌─────────────┴──────────────┐
         │                            │
   CloudFront (OAC)             Application Load Balancer  (HTTPS :443, HTTP→HTTPS)
         │                            │  path-based routing:
   S3 (private, SPA)                  │    /api/*         → :8000 (Django, health /api/items/)
                                      │    /chat, /chat/* → :8001 (chatbot, health /health)
                                      │    default        → :8000
                                      ▼
                        Auto Scaling group (EC2, private subnets)
                        each server runs both containers
                                      │
                                      ▼
                            RDS MySQL 8.4 (private subnets)
```

Two stacks, coupled only through CloudFormation Exports:

- **`vpc_dev.yaml`** — VPC `10.1.0.0/16`, 2 AZs, public + private subnets, an
  Internet Gateway, and a single NAT Gateway (so the private servers can reach
  Docker Hub). Exports `VPCId`, the two public and two private subnet ids.
- **`backend_infra.yaml`** — the application tier. Imports the VPC exports via
  its `NetworkStackName` parameter, which **must equal the VPC stack's name**.
  Creates:
  - Internet-facing **ALB** (HTTPS listener with ACM cert; HTTP→HTTPS redirect)
    with path rules for the API (`:8000`) and chatbot (`:8001`, sticky sessions).
  - **Launch template + Auto Scaling group** of Ubuntu EC2 servers in the
    private subnets, each running the `web_backend` and `chatbot` containers
    (see [How a server starts](#how-a-server-starts)).
  - **RDS MySQL 8.4** (`db.t3.micro`, encrypted, 7-day backups) reachable only
    from the servers' security group.
  - **S3 bucket** (private) + **CloudFront** distribution (OAC, SPA error
    routing: 403/404 → `/index.html`) for the frontend.

## How a server starts

Nothing is pre-installed on the servers. When the Auto Scaling group launches
one, the user data script in `backend_infra.yaml`:

1. Installs Docker and `cfn-signal`.
2. Writes `/srv/.env` with the database endpoint and the secrets passed to the
   stack as parameters.
3. Writes `/srv/compose.yaml` that runs `WebBackendImage:DockerImageTag` and
   `ChatbotImage:DockerImageTag`, then starts it with `docker compose up -d`.
   Each container's `setup.sh` writes its own `.env`, prepares the database,
   and starts its service.
4. Waits until `http://localhost:8000/api/items/` and
   `http://localhost:8001/health` both answer (up to about 5 minutes each).
5. Sends `cfn-signal` with the result.

CloudFormation waits up to **20 minutes** for each server's signal. If a server
reports failure or never signals, the deploy fails and **rolls back
automatically**.

## Prerequisites (one-time)

Create these before your first deploy. The templates don't create them.

1. **ACM certificate in `us-east-1`** covering your frontend domain and your API
   domain. CloudFront and the load balancer both use it, which is why
   everything deploys to `us-east-1`.
2. **IAM instance profile** for the EC2 servers, with SSM access so you can log
   in to a server to debug.
3. **Globally unique S3 bucket name** for the frontend.
4. **Domain in Route 53** for the DNS records.
5. **Docker Hub account** for the images `<user>/web_backend` and
   `<user>/chatbot`. With Option A, GitHub Actions builds and pushes them for you.
6. **AWS user for deploying** (an IAM user with access keys). It needs
   permissions for CloudFormation, EC2, Auto Scaling, Elastic Load Balancing,
   RDS, S3, and CloudFront, plus `iam:PassRole` on the instance profile's role
   (the launch template attaches that role to every server).
7. *(Optional)* **EC2 key pair.** The `KeyPairName` parameter exists but isn't
   attached to the servers yet, so use SSM to log in.

## Option A: Automatic deploys with GitHub Actions

The workflow is
[`.github/workflows/main_test_build_deploy.yaml`](../.github/workflows/main_test_build_deploy.yaml).

| When | What happens |
|---|---|
| A pull request into `main` is opened or updated | Runs the Django tests only. |
| A commit lands on `main`, or you click **Run workflow** on `main` | Runs the full pipeline below. |

The full pipeline:

1. Runs the Django tests. If they fail, it stops here.
2. Builds the `web_backend` and `chatbot` images, tags them with the commit
   SHA, and pushes them to Docker Hub.
3. Writes `deploy/cloud_formation_templates/.env` from the GitHub settings
   below and runs `deploy.sh <commit SHA>`. The servers are replaced one at a
   time with the new images.
4. Builds the frontend with the `VITE_*` settings, uploads it to S3, and clears
   the CloudFront cache.

Only one deploy runs at a time; a newer one waits for the current one.

### One-time setup

In GitHub, open the repo → **Settings → Environments → New environment**, name
it `dev`, and add the following.

**Environment variables** (not secret):

| Name | Example | What it's for |
|---|---|---|
| `DOCKERHUB_USERNAME` | `loc109` | Docker Hub login and image names |
| `WEBBACKENDIMAGE` | `loc109/web_backend` | image the servers run |
| `CHATBOTIMAGE` | `loc109/chatbot` | image the servers run |
| `VPC_STACKNAME` | `n-stack-restaurant-vpc` | VPC stack name |
| `VPC_REGION` | `us-east-1` | VPC stack region |
| `BACKEND_STACKNAME` | `n-stack-restaurant-backend` | application stack name |
| `BACKEND_REGION` | `us-east-1` | application stack region; also used to sign in to AWS |
| `NETWORKSTACKNAME` | `n-stack-restaurant-vpc` | must equal `VPC_STACKNAME` |
| `PROJECTNAME` | `restaurant-cfn` | prefix for resource names |
| `S3BUCKETNAME` | `restaurant-front-cfn.loc109.click` | frontend bucket |
| `CLOUDFRONTALIAS` | `restaurant.loc109.click` | frontend domain |
| `VITE_BACKEND_URL` | `https://restaurant-api.loc109.click/api` | where the frontend calls the API (no trailing `/`) |
| `VITE_CHATBOT_URL` | `wss://restaurant-api.loc109.click/chat` | where the frontend connects to the chatbot |
| `VITE_DEBUG` | `false` | chatbot debug logging in the browser |

**Environment secrets:**

| Name | What it is |
|---|---|
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | access keys of the deploy user (prerequisite 6) |
| `DOCKERHUB_TOKEN` | Docker Hub access token with Read & Write access |
| `DBNAME` | database name, e.g. `the_restaurant` |
| `DBUSERNAME` | database admin user, e.g. `admin` |
| `DBPASSWORD` | database password, at least 8 characters |
| `BACKENDADMINUSERNAME`, `BACKENDADMINPASSWORD` | Django admin login, created on first start |
| `DJANGOKEY` | Django `SECRET_KEY` |
| `OPENROUTERKEY` | OpenRouter API key |
| `PINECONEKEY` | Pinecone API key |
| `IAMINSTANCEPROFILE` | instance profile name, e.g. `n-role-ec2-with-ssm` |
| `KEYPAIRNAME` | EC2 key pair name (not used by the servers yet) |

> **Warning:** don't change `DBNAME` or `DBUSERNAME` after the first deploy.
> CloudFormation would replace the database with a new, empty one and delete
> the old one.

If a `VITE_*` variable is missing, the deploy still succeeds, but the website
calls an `undefined` URL. Check the site after the first run.

**Recommended:** in **Settings → Branches**, add a rule for `main` with
**Require status checks to pass before merging** and select `Test`.

## Option B: Manual deploys from your machine

You need the AWS CLI v2 signed in to the deploy account with its default region
set to `us-east-1`, plus Docker and Node.js 20.19+.

### 1. Fill in the settings

Create `deploy/cloud_formation_templates/.env`. Every script reads this file:

```bash
# Stacks
VPC_STACKNAME=n-stack-restaurant-vpc
VPC_REGION=us-east-1
BACKEND_STACKNAME=n-stack-restaurant-backend
BACKEND_REGION=us-east-1
NetworkStackName=n-stack-restaurant-vpc      # must equal VPC_STACKNAME
ProjectName=restaurant-cfn

# Images the servers run
WebBackendImage=loc109/web_backend
ChatbotImage=loc109/chatbot

# Frontend
S3BucketName=<globally-unique-bucket-name>
CloudFrontAlias=<frontend domain>

# EC2
IAMInstanceProfile=<instance profile name>
KeyPairName=<key pair name>

# Database
DBName=the_restaurant
DBUsername=admin
DBPassword='<at least 8 characters>'

# App secrets
BackendAdminUsername=<django admin user>
BackendAdminPassword='<django admin password>'
DjangoKey='<django secret key>'
OpenRouterKey=<openrouter api key>
PineconeKey=<pinecone api key>
```

The scripts load this file with bash, so wrap any value that contains `$` or
other special characters in single quotes, and don't use spaces in values.

### 2. Build and push the images

Skip this if the images for the tag you want already exist on Docker Hub. From
the repo root:

```bash
docker login
docker build -t loc109/web_backend:v0.4 backend
docker build -t loc109/chatbot:v0.4 chatbot_backend
docker push loc109/web_backend:v0.4
docker push loc109/chatbot:v0.4
```

Use a **new tag for every release** (`v0.4`, `v0.5`, …). If you reuse a tag,
CloudFormation sees no change and the servers keep the old image.

### 3. Deploy the stacks

```bash
cd deploy/cloud_formation_templates
bash ../scripts/deploy.sh v0.4
```

The image tag is required. The script deploys the VPC stack first, then the
application stack, and waits for each to finish. The first deploy can take
half an hour or more, because RDS and CloudFront are slow to create.

### 4. Upload the frontend

First set the production URLs in `frontend/restaurant/.env` (the same values as
the `VITE_*` table above), and run `npm install` in `frontend/restaurant` once.
Then, still in `deploy/cloud_formation_templates`:

```bash
bash ../scripts/uploadS3.sh
```

### 5. Point your domains (first deploy only)

In Route 53, create alias records:

- your frontend domain (`CloudFrontAlias`) → the CloudFront distribution
- your API domain (e.g. `restaurant-api.loc109.click`) → the load balancer

The stack already attaches `CloudFrontAlias` to the distribution. To look up
the CloudFront domain and the load balancer's DNS name:

```bash
aws cloudformation describe-stacks --stack-name n-stack-restaurant-backend \
  --query "Stacks[0].Outputs" --output table
```

### Testing the containers on one machine

`scripts/compose.yaml` runs both images against a MySQL server on your own
machine (through `host.docker.internal`, which Docker Desktop provides). Put a
`.env` next to it with `BackendAdminUsername`, `BackendAdminPassword`,
`DBName`, `DBUsername`, `DBPassword`, `DjangoKey`, `OpenRouterKey`, and
`PineconeKey`, set the image tags in the file, then run `docker compose up -d`
in `deploy/scripts`.

## Updating and rolling back

- **Releasing new code:** deploy with a new image tag. Option A does this on
  every merge to `main`. CloudFormation replaces the servers **one at a time**,
  and each new server must pass its health checks and signal within 20 minutes.
  At least one server keeps handling traffic throughout.
- **If a new server fails,** the deploy stops and **rolls back automatically**.
  The stack ends in `UPDATE_ROLLBACK_COMPLETE`, and the previous version keeps
  running.
- **If a release deploys fine but has a bug,** CloudFormation can't undo a
  successful deploy. Deploy the previous tag again (`bash ../scripts/deploy.sh
  v0.3`), or with Option A, revert the commit on `main`.
- **Database migrations are never rolled back.** The first new server runs
  `migrate` on the shared database while an old server is still running. Keep
  migrations backward compatible: add new columns or tables in one release,
  and remove old ones in a later one.
- **Changing `DBName` or `DBUsername` replaces the database** with a new, empty
  one, and the old one is deleted. Don't change them after the first deploy.
- **Changing `DBPassword`** changes the RDS password right away. Servers still
  on the old password lose database access until they're replaced.

## Troubleshooting

**A deploy failed.** List the failure events. They're newest first, so the root
cause is the **last** row:

```bash
aws cloudformation describe-stack-events --stack-name n-stack-restaurant-backend \
  --query "StackEvents[?contains(ResourceStatus,'FAILED')].[Timestamp,LogicalResourceId,ResourceStatusReason]" \
  --output table
```

**"Received FAILURE signal" or a signal timeout.** A server's health checks
failed. Read that server's boot log. The instance id is in the event message,
and the log is still available for a while after the server is terminated:

```bash
aws ec2 get-console-output --instance-id <instance-id> --latest --output text
```

On a running server (connect with SSM), the same log is in
`/var/log/cloud-init-output.log`.

**The stack is in `ROLLBACK_COMPLETE`.** Its first create failed, and it can't be
updated. Delete it, then deploy again:

```bash
aws cloudformation delete-stack --stack-name n-stack-restaurant-backend --region us-east-1
```

**The website calls `undefined/...`.** A `VITE_*` value was empty when the
frontend was built.

**"No changes to deploy."** Nothing changed, for example because you redeployed
the same image tag.

## Tearing down

```bash
cd deploy/cloud_formation_templates
bash ../scripts/deleteStacks.sh    # empties the S3 bucket, deletes the app stack, then the VPC stack
```

Then delete the Route 53 records that pointed at CloudFront and the load
balancer. Deleting the application stack **also deletes the database**.

## Minimal demo stack (older setup)

`minimal_backend.yaml` is a cheaper version for demos: one EC2 server in the
default VPC (no custom VPC or Auto Scaling group), plus the load balancer, RDS,
S3, and CloudFront. It uses the **older, non-Docker setup**: at boot the server
clones this repo, checks out the **`deploy_aws`** branch, and runs each
service's `setup.sh` directly. Push your code to `deploy_aws` before deploying
it.

> **Warning:** `deploy_minimal.sh` uses the same `BACKEND_STACKNAME` from `.env`
> as the full deploy. Set a different `BACKEND_STACKNAME` first, or it will try
> to turn your full stack into the minimal one.

```bash
cd deploy/cloud_formation_templates
bash ../scripts/deploy_minimal.sh
bash ../scripts/uploadS3.sh
bash ../scripts/delete_minimal.sh    # tear it down
```

## Security notes

- **Secrets reach the servers through the user data script.** CloudFormation
  hides parameters marked `NoEcho`, but anyone who can view an instance's user
  data in the EC2 console, or any process on the server, can read them. That's
  acceptable for a demo; for production, store them in SSM Parameter Store or
  Secrets Manager and fetch them at boot.
- **The Docker images are public on Docker Hub,** so they must never contain
  secrets. Both Dockerfiles copy their whole folder, and `.dockerignore`
  (`**/.env*`) is what keeps `.env` files out. GitHub Actions builds are also
  safe because the runner only has committed files.
- **The deploy user's access keys never expire.** Give that user only the
  permissions listed in the prerequisites, and if a key ever leaks, deactivate
  it in IAM right away.
- **The repository is public.** Never commit `.env` files, and never put real
  values in documentation.
