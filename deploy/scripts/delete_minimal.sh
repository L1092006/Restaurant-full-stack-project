#! /bin/bash
# Empty the S3 bucket and delete the minimal stack

# Cd to the templates directory
FILE_LOCATION=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd $FILE_LOCATION/../cloud_formation_templates


if [ -f .env ]; then
  . .env
fi

# Empty the S3 bucket
aws s3 rm s3://$S3BucketName --recursive



# Delete all the stacks

aws cloudformation delete-stack --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION