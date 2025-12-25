# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name = "${var.project_name}-dlq"

  tags = {
    Name        = "${var.project_name}-dlq"
    Environment = "production"
  }
}

# Main processing queue
resource "aws_sqs_queue" "processing" {
  name                       = "${var.project_name}-processing"
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.dlq_max_receive_count
  })

  tags = {
    Name        = "${var.project_name}-processing"
    Environment = "production"
  }
}

# Allow S3 to send messages to SQS
resource "aws_sqs_queue_policy" "processing" {
  queue_url = aws_sqs_queue.processing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.processing.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.documents.arn
          }
        }
      }
    ]
  })
}

# S3 event notification to SQS
resource "aws_s3_bucket_notification" "documents" {
  bucket = aws_s3_bucket.documents.id

  queue {
    queue_arn = aws_sqs_queue.processing.arn
    events    = ["s3:ObjectCreated:*"]
    filter_prefix = "uploads/"
  }

  depends_on = [aws_sqs_queue_policy.processing]
}

