terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Security group
resource "aws_security_group" "uav_sg" {
  name        = "uav-monitoring-sg"
  description = "UAV monitoring security group"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "uav-monitoring-sg"
  }
}

# EC2 instance
resource "aws_instance" "uav_server" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.uav_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose-plugin
              systemctl start docker
              systemctl enable docker
              EOF

  tags = {
    Name = "uav-monitoring"
  }
}

# Outputs
output "public_ip" {
  value       = aws_instance.uav_server.public_ip
  description = "EC2 public IP address"
}

output "dashboard_url" {
  value       = "http://${aws_instance.uav_server.public_ip}:5000"
  description = "UAV dashboard URL"
}