#! /bin/bash
# Build and upload the react app to S3 bucket
# Import env variables from .env file
if [ -f .env ]; then
  . .env
fi

FILE_LOCATION=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd $FILE_LOCATION/../../frontend/restaurant/
npm run build
aws s3 sync dist/ s3://$S3BucketName --delete

# Fetch the cloudfront distribution ID from the backend stack outputs
CloudFrontID=$(aws cloudformation describe-stacks --stack-name $BACKEND_STACKNAME --query "Stacks[0].Outputs[?OutputKey=='CloudFrontID'].OutputValue" --output text)

# Invalidate the CloudFront distribution to clear the cache and serve the updated content
aws cloudfront create-invalidation --distribution-id $CloudFrontID --paths "/*"
