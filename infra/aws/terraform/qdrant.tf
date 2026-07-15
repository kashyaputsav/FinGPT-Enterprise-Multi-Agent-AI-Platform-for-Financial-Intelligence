/*
Self-hosted Qdrant running as its own ECS Fargate service, reachable from the
API service via AWS Cloud Map private DNS (qdrant.<project>.local:6333).
For a lighter-weight setup, swap this out for a Qdrant Cloud cluster and just
point QDRANT_URL / QDRANT_API_KEY at it in ecs.tf instead.
*/

resource "aws_service_discovery_private_dns_namespace" "internal" {
  name = "${var.project_name}.local"
  vpc  = aws_vpc.main.id
}

resource "aws_service_discovery_service" "qdrant" {
  name = "qdrant"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.internal.id
    dns_records {
      ttl  = 10
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_efs_file_system" "qdrant_storage" {
  encrypted = true
  tags      = { Name = "${var.project_name}-qdrant-efs" }
}

resource "aws_efs_mount_target" "qdrant" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.qdrant_storage.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.qdrant_efs.id]
}

resource "aws_security_group" "qdrant_efs" {
  name        = "${var.project_name}-qdrant-efs-sg"
  description = "Allow NFS from the qdrant ECS task"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.qdrant.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "qdrant" {
  name        = "${var.project_name}-qdrant-sg"
  description = "Allow inbound 6333 only from the API ECS service"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6333
    to_port         = 6333
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "qdrant" {
  family                   = "${var.project_name}-qdrant"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  volume {
    name = "qdrant-storage"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.qdrant_storage.id
    }
  }

  container_definitions = jsonencode([
    {
      name      = "qdrant"
      image     = "qdrant/qdrant:v1.11.3"
      essential = true
      portMappings = [{ containerPort = 6333, protocol = "tcp" }]
      mountPoints = [
        { sourceVolume = "qdrant-storage", containerPath = "/qdrant/storage" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "qdrant"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "qdrant" {
  name            = "${var.project_name}-qdrant-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.qdrant.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.qdrant.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.qdrant.arn
  }
}
