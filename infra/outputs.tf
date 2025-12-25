output "s3_bucket_name" {
  description = "Name of the S3 bucket for document uploads"
  value       = aws_s3_bucket.documents.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.documents.arn
}

output "sqs_queue_url" {
  description = "URL of the processing SQS queue"
  value       = aws_sqs_queue.processing.url
}

output "sqs_queue_arn" {
  description = "ARN of the processing SQS queue"
  value       = aws_sqs_queue.processing.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.processor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.processor.arn
}

output "dlq_url" {
  description = "URL of the dead letter queue"
  value       = aws_sqs_queue.dlq.url
}

