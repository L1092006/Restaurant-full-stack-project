#! /bin/bash

# Import env variables from .env file
if [ -f .env ]; then
  . .env
fi

echo "Deploying VPC stack"
# VPC stack
aws cloudformation deploy --template-file vpc_dev.yaml \
  --stack-name $VPC_STACKNAME --region $VPC_REGION \
  --parameter-overrides ProjectName=$ProjectName

echo "Wait for  the VPC stack to be created"
aws cloudformation wait stack-create-complete --stack-name $VPC_STACKNAME --region $VPC_REGION
if [ $? -ne 0 ]; then
    echo "$VPC_STACKNAME failed"
    exit 1
fi
echo "VPC stack created successfully"

echo "##############################################################################################################"
echo "Deploying backend stack"
#  App stack
aws cloudformation deploy --template-file cloud_formation_templates/backend_infra.yaml \
  --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION \
  --parameter-overrides ProjectName=$ProjectName NetworkStackName=$VPC_STACKNAME \
    DBPassword=$DBPassword BackendAdminUsername=$BackendAdminUsername BackendAdminPassword=$BackendAdminPassword \
    DjangoKey=$DjangoKey PineconeKey=$PineconeKey OpenRouterKey=$OpenRouterKey S3BucketName=$S3BucketName \
    CloudALias=$CloudALias KeyPairName=$KeyPairName IAMInstanceProfile=$IAMInstanceProfile

echo "Wait for the backend stack to be created"
aws cloudformation wait stack-create-complete --stack-name $BACKEND_STACKNAME --region $BACKEND_REGION
if [ $? -ne 0 ]; then
    echo "$BACKEND_STACKNAME failed"
    exit 1
fi
echo "Backend stack created successfully"