#!/bin/bash

echo "Create Inital Code bucket"
aws cloudformation deploy --template-file s3.yaml --stack-name aws-mlops-s3-stack
export BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name aws-mlops-s3-stack | jq -r '.Stacks[0].Outputs[0].OutputValue')
echo $BUCKET_NAME  

echo "Upload inital model and data"
aws s3 cp src s3://${BUCKET_NAME}/src --recursive

echo "Upload code"
zip -r code.zip * 
aws s3 cp code.zip s3://${BUCKET_NAME}/code.zip

echo "Deploy CICD"
aws cloudformation deploy --template-file cicd.yaml --stack-name aws-mlops-cicd-stack --capabilities CAPABILITY_NAMED_IAM