#! /bin/bash

# Empty the S3 bucket
aws s3 rm s3://$S3BucketName --recursive



# Delete all the stacks

aws cloudformation delete-stack --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION
aws cloudformation wait stack-delete-complete --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION
aws cloudformation delete-stack --stack-name $VPC_STACKNAME --region $VPC_REGION
