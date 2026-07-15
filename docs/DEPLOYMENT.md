# Deploying FinGPT Enterprise to AWS

This walks through a first-time production deployment: VPC → RDS/Redis/Qdrant →
ECR → ECS Fargate → ALB, wired together with Terraform, plus the GitHub
Actions pipeline that automates every subsequent deploy.

## 0. Prerequisites

- AWS account with admin (or sufficiently scoped) credentials configured locally
  (`aws configure` or SSO)
- Terraform >= 1.7
- Docker
- A registered domain (optional but recommended) + an ACM certificate for it in
  the region you deploy to (`ap-south-1` by default)

## 1. Provision infrastructure with Terraform

```bash
cd infra/aws/terraform
cp prod.tfvars.example prod.tfvars   # fill in acm_certificate_arn, container_image, etc.

export TF_VAR_db_password="<choose a strong password>"
export TF_VAR_jwt_secret_key="$(openssl rand -hex 32)"
export TF_VAR_openai_api_key="sk-..."

terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

This creates: a VPC with public/private subnets across 2 AZs, a NAT gateway,
RDS Postgres, ElastiCache Redis, a self-hosted Qdrant ECS service (via EFS +
Cloud Map service discovery), an S3 bucket for documents, an ECR repository,
an ECS Fargate cluster/service, an ALB with HTTP→HTTPS redirect, IAM roles
scoped to least privilege, and Secrets Manager entries for JWT/DB/OpenAI
secrets.

> The very first `apply` will fail to start real ECS tasks successfully
> because `container_image` doesn't exist in ECR yet — that's expected. Push
> an image first (step 2), then let the ECS service pick it up.

## 2. Build and push the first image

```bash
cd infra/aws/ecs
./deploy.sh initial
```

This logs into ECR, builds `backend/Dockerfile`, pushes `:initial` and
`:latest`, and forces a new ECS deployment.

## 3. Point your domain at the ALB

```bash
terraform output alb_dns_name
```

Create a CNAME (or an ALIAS record if using Route 53) from your domain to that
ALB DNS name.

## 4. Run database migrations

Migrations run via Alembic. The simplest approach for a first deploy is a
one-off ECS task using the same image:

```bash
aws ecs run-task \
  --cluster fingpt-enterprise-cluster \
  --task-definition fingpt-enterprise-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<private-subnet-ids>],securityGroups=[<ecs-sg-id>]}" \
  --overrides '{"containerOverrides":[{"name":"fingpt-enterprise-api","command":["alembic","upgrade","head"]}]}'
```

## 5. Set up CI/CD (GitHub Actions)

1. Create an IAM role for GitHub's OIDC provider with permission to push to
   ECR and update the ECS service (see AWS docs: "Configuring OpenID Connect
   in Amazon Web Services").
2. Add its ARN as a repo secret: `AWS_DEPLOY_ROLE_ARN`.
3. Every push to `main` now runs `.github/workflows/ci-cd.yml`: lint → test →
   build → push to ECR → render a new task definition → deploy to ECS with
   `wait-for-service-stability: true`.

## 6. Verify

```bash
curl https://your-domain.com/api/v1/health
# {"status": "ok"}

curl https://your-domain.com/docs   # interactive API docs (disabled in production by default —
                                     # see app/main.py docs_url logic; enable if you want it public)
```

## Cost-saving notes for a portfolio deployment

- Use `db.t4g.micro` / `cache.t4g.micro` (already the defaults) and a single
  NAT gateway rather than one per AZ.
- Set `desired_count = 1` and skip the autoscaling policy if you don't need
  redundancy for a demo.
- Tear down with `terraform destroy -var-file=prod.tfvars` when not actively
  demoing it — RDS + NAT gateway are the main hourly costs.
