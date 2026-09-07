# Steps to deploy
**Deploy the stacks**:

`. scripts/deploy.sh`

**Change frontenv env to use the correct backend API**

**Build and upload the frontend  code to s3**:

`. scripts/uploadS3.sh`

**In AWS console, go to Route53 and update the record to point to the newly created ALB**

# To delete
**Delete the stacks**

`. scripts/deleteStack.sh`

**In AWS console, go to Route53 to delete the records pointing to the CloudFront distribution**


