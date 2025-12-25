# AWS Proof Layer - RAG Pipeline

A minimal, enterprise-legible pipeline demonstrating document ingestion, embedding, and retrieval with AWS serverless services and Supabase Postgres (pgvector).

## Architecture

```
S3 → SQS → Lambda → Supabase (pgvector) → FastAPI /ask
```

**Flow:**
1. Client requests presigned S3 URL from FastAPI `/presign`
2. Client uploads document to S3
3. S3 event triggers SQS message
4. Lambda worker processes: chunks text, generates embeddings, stores in Supabase
5. Client queries via FastAPI `/ask` endpoint (similarity search with pgvector)

## Local Run

Start the API server:
```powershell
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://localhost:8000`

## Deploy

From `infra/` directory:
```powershell
cd infra
terraform init
terraform apply
```

This creates S3 bucket, SQS queue, Lambda function, and IAM roles. Configure variables via `terraform.tfvars` (gitignored).

## Smoke Test

**1. Get presigned URL:**
```powershell
$body = @{filename="test.txt"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/presign" -Method POST -Body $body -ContentType "application/json"
```

**2. Upload to S3 (use `url` from response):**
```powershell
$url = "https://..." # from presign response
$content = "This is a test document about machine learning."
Invoke-RestMethod -Uri $url -Method PUT -Body $content -ContentType "text/plain"
```

**3. Query knowledge base:**
```powershell
$body = @{question="What is machine learning?"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -Body $body -ContentType "application/json"
```

## Security / Secrets

- **Never commit `.env`** - it contains sensitive credentials
- Use `.env.example` as a template
- Rotate keys immediately if accidentally leaked
- Ensure `.gitignore` excludes `.env`, `*.tfvars`, and other secret files

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

