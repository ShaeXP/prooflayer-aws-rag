variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "proof-layer"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds (should be >= lambda timeout)"
  type        = number
  default     = 330
}

variable "dlq_max_receive_count" {
  description = "Maximum number of receives before message goes to DLQ"
  type        = number
  default     = 3
}

variable "supabase_url" {
  description = "Supabase project URL (e.g., https://xxx.supabase.co)"
  type        = string
  sensitive   = false
}

variable "supabase_service_role_key" {
  description = "Supabase service role key for API access"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for embeddings"
  type        = string
  sensitive   = true
}

