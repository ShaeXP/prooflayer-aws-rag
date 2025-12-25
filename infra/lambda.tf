# Archive Lambda code
# Zip from parent to include worker/ as package folder, exclude everything else
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/.."
  output_path = "${path.module}/build/worker.zip"
  excludes = [
    # Python cache and virtual environments
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    ".env.*",
    # Project directories to exclude
    "api",
    "db",
    "infra",
    "scripts",
    "tests",
    "test",
    "deployed_lambda",
    "build",
    # Files to exclude
    "*.md",
    "*.txt",
    "*.toml",
    "*.json",
    "*.log",
    ".git",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".pre-commit-config.yaml",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    # Only worker/ directory will be included (not in excludes)
  ]
}

# Lambda function
resource "aws_lambda_function" "processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-processor"
  role            = aws_iam_role.lambda.arn
  handler         = "worker.lambda_handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      SUPABASE_URL            = var.supabase_url
      SUPABASE_SERVICE_ROLE_KEY = var.supabase_service_role_key
      EMBEDDING_MODE          = "openai"
      OPENAI_API_KEY         = var.openai_api_key
    }
  }

  tags = {
    Name        = "${var.project_name}-processor"
    Environment = "production"
  }
}

# Lambda event source mapping from SQS
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.processing.arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 1
  enabled          = true
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.processor.function_name}"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-lambda-logs"
    Environment = "production"
  }
}

