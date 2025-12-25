# AWS Proof Layer - RAG Pipeline

A minimal, enterprise-legible pipeline demonstrating document ingestion, embedding, and retrieval with AWS serverless services and Supabase Postgres (pgvector).

## Architecture

```
Client -> FastAPI /presign -> S3 Upload
                              |
                              v
                         S3 Event -> SQS -> Lambda Worker
                                           |
                                           v
                                    Chunk + Embed -> Supabase Postgres (pgvector)
                                                              |
                                                              v
Client -> FastAPI /ask -> Similarity Search -> Citations + Answer (or Refusal)
```

## Prerequisites

- Python 3.11
- Terraform >= 1.0
- AWS CLI configured with credentials
- Supabase project with Postgres database
- PowerShell (for scripts)

## Local Setup

1. **Clone and create virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```powershell
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Run database migrations:**
   ```powershell
   # Print migrations for easy copy/paste
   .\scripts\print_migrations.ps1
   ```
   - Copy the SQL output (not file paths) from the script
   - Open Supabase dashboard → SQL Editor
   - Execute MIGRATION 001 first, then MIGRATION 002

## Running Locally

### Start the API server:
```powershell
.\scripts\run_local_api.ps1
```

The API will be available at `http://localhost:8000`

### Test endpoints:
- `GET /health` - Health check
- `POST /presign` - Get presigned S3 upload URL
- `POST /ask` - Query the knowledge base

## Deploying Infrastructure

1. **Initialize Terraform:**
   ```powershell
   cd infra
   terraform init
   ```

2. **Review plan:**
   ```powershell
   terraform plan
   ```

3. **Configure Terraform variables:**
   Create `terraform.tfvars` in `infra/`:
   ```hcl
   supabase_url = "https://your-project.supabase.co"
   supabase_service_role_key = "your_service_role_key"
   ```

4. **Apply infrastructure:**
   ```powershell
   terraform apply
   ```
   This creates:
   - S3 bucket, SQS queue, Lambda function
   - Lambda layer with OpenAI SDK (built automatically)
   - Lambda environment variables (from terraform.tfvars)

5. **Get outputs:**
   ```powershell
   terraform output
   ```

6. **Update `.env` with outputs:**
   - `S3_BUCKET_NAME` from terraform output
   - Ensure `AWS_REGION` matches your terraform region

## Environment Variables

Required variables (see `.env.example`):

- `AWS_REGION` - AWS region for resources
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `S3_BUCKET_NAME` - S3 bucket name (from terraform output)
- `SUPABASE_URL` - Supabase project URL (e.g., `https://xxx.supabase.co`) or direct Postgres connection string (e.g., `postgresql://postgres.xxx:key@db.xxx.supabase.co:5432/postgres`)
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (required if using project URL)
- `SUPABASE_USE_POOLER` - Set to `true` to use pooler connection (default: `false`, uses direct connection)
- `EMBEDDING_MODE` - `fake` (default) or `openai`
- `OPENAI_API_KEY` - Required if `EMBEDDING_MODE=openai`
- `SIMILARITY_THRESHOLD` - Cosine similarity threshold (0.0-1.0, default 0.7)

**Supabase Connection:**
- By default, uses **direct connection** (`db.<project-ref>.supabase.co:5432`) - recommended for local development
- Set `SUPABASE_USE_POOLER=true` to use pooler connection (`aws-0-<region>.pooler.supabase.com:6543`) - for serverless/Lambda
- You can also provide a full `postgresql://` connection string directly in `SUPABASE_URL`

## Manual Testing Workflow

1. **Start local API:**
   ```powershell
   .\scripts\run_local_api.ps1
   ```

2. **Get presigned URL:**
   ```powershell
   $body = @{filename="test.txt"} | ConvertTo-Json
   Invoke-RestMethod -Uri "http://localhost:8000/presign" -Method POST -Body $body -ContentType "application/json"
   ```
   Save the `trace_id`, `key`, and `url` from the response.

3. **Upload file to S3:**
   ```powershell
   $url = "..." # from presign response
   $content = "This is a test document about machine learning and artificial intelligence."
   Invoke-RestMethod -Uri $url -Method PUT -Body $content -ContentType "text/plain"
   ```

4. **Wait for Lambda processing:**
   - Check CloudWatch logs for the Lambda function
   - Or wait ~30 seconds for processing

5. **Query the knowledge base:**
   ```powershell
   $body = @{question="What is machine learning?"; top_k=5} | ConvertTo-Json
   Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -Body $body -ContentType "application/json"
   ```

## Testing

Run tests:
```powershell
.\scripts\test.ps1
```

Tests include:
- Trace ID generation and format
- Chunking logic
- Refusal logic for weak matches

## Formatting

Format code:
```powershell
.\scripts\fmt.ps1
```

## Cost Notes

This is a serverless architecture:
- **S3**: Pay per GB stored and requests
- **SQS**: Pay per request (first 1M requests/month free)
- **Lambda**: Pay per invocation and compute time (1M free requests/month)
- **CloudWatch Logs**: Pay per GB ingested and stored
- **Supabase**: Free tier available, but pgvector queries consume compute

**Warning**: CloudWatch Logs can accumulate quickly. Set up log retention policies or delete old logs periodically.

## Project Structure

```
/
  api/              # FastAPI application
  worker/           # Lambda worker functions
  db/               # SQL migrations
  infra/            # Terraform configuration
  scripts/          # PowerShell utility scripts
```

## Trace ID Propagation

Every request/job has a `trace_id` (UUID) that propagates through:
- API `/presign` response
- S3 object key path
- SQS message attributes
- Lambda logs (structured JSON)
- Database rows (documents and chunks)

This enables end-to-end traceability for debugging and monitoring.

