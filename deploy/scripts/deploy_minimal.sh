#! /bin/bash

# Cd to the templates directory
FILE_LOCATION=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd $FILE_LOCATION/../cloud_formation_templates

# Import env variables from .env file
if [ -f .env ]; then
  . .env
fi

echo "Deploying backend stack"
#  App stack
aws cloudformation deploy --template-file minimal_backend.yaml \
  --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION \
  --parameter-overrides ProjectName=restaurant-min DBPassword=$DBPassword \
  BackendAdminUsername=$BackendAdminUsername BackendAdminPassword=$BackendAdminPassword \
    DjangoKey=$DjangoKey PineconeKey=$PineconeKey OpenRouterKey=$OpenRouterKey S3BucketName=$S3BucketName \
    CloudALias=$CloudALias KeyPairName=$KeyPairName IAMInstanceProfile=$IAMInstanceProfile

echo "Wait for the backend stack to be created"
aws cloudformation wait stack-create-complete --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION
if [ $? -ne 0 ]; then
    echo "$BACKEND_STACKNAME failed"
    exit 1
fi
echo "Backend stack created successfully"