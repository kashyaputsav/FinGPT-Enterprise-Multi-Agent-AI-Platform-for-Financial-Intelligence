#!/usr/bin/env bash
# Manual build-push-deploy helper (CI/CD does this automatically — see
# .github/workflows/deploy.yml — use this for local/manual deploys or debugging).
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-south-1}"
PROJECT_NAME="${PROJECT_NAME:-fingpt-enterprise}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-api"
IMAGE_TAG="${1:-$(git rev-parse --short HEAD)}"

echo "==> Logging in to ECR: ${ECR_REPO}"
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "==> Building image ${ECR_REPO}:${IMAGE_TAG}"
docker build -t "${ECR_REPO}:${IMAGE_TAG}" -t "${ECR_REPO}:latest" ../../backend

echo "==> Pushing image"
docker push "${ECR_REPO}:${IMAGE_TAG}"
docker push "${ECR_REPO}:latest"

echo "==> Forcing new ECS deployment"
aws ecs update-service \
  --cluster "${PROJECT_NAME}-cluster" \
  --service "${PROJECT_NAME}-service" \
  --force-new-deployment \
  --region "${AWS_REGION}" > /dev/null

echo "==> Waiting for service to stabilize"
aws ecs wait services-stable \
  --cluster "${PROJECT_NAME}-cluster" \
  --services "${PROJECT_NAME}-service" \
  --region "${AWS_REGION}"

echo "==> Deployed ${ECR_REPO}:${IMAGE_TAG} successfully"
