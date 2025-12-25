# Run Order - Quick Start Guide

## Prerequisites Checklist

- [ ] Python 3.11 installed
- [ ] Terraform >= 1.0 installed
- [ ] AWS CLI configured with credentials
- [ ] Supabase project created
- [ ] Supabase database connection details ready

## Step-by-Step Execution Order

### 1. Local Setup

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your values (see below)
```

### 2. Database Setup

1. Run the migration script to print SQL:
   ```powershell
   .\scripts\print_migrations.ps1
   ```

2. Copy the SQL output (not the file paths) from the script output

3. Open Supabase dashboard → SQL Editor

4. Execute migrations in order:
   - First: Copy and paste the SQL from "MIGRATION 001" section and execute
   - Second: Copy and paste the SQL from "MIGRATION 002" section and execute

5. Note your connection details:
   - Project URL: `https://xxx.supabase.co`
   - Service Role Key: (from Settings → API)

### 3. Configure Environment Variables

Edit `.env` with:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=will-be-set-after-terraform

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

EMBEDDING_MODE=fake
SIMILARITY_THRESHOLD=0.7
```

### 4. Deploy Infrastructure

```powershell
cd infra

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates S3, SQS, Lambda)
terraform apply

# Get outputs
terraform output s3_bucket_name
```

### 5. Update .env with Terraform Outputs

```powershell
# Update S3_BUCKET_NAME in .env with the output from step 4
```

### 6. Configure Terraform Variables

Create `terraform.tfvars` in `infra/` directory:

```hcl
supabase_url = "https://your-project.supabase.co"
supabase_service_role_key = "your_service_role_key"
```

Or set via environment variables:
```powershell
$env:TF_VAR_supabase_url = "https://your-project.supabase.co"
$env:TF_VAR_supabase_service_role_key = "your_service_role_key"
```

**Note:** Lambda environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, EMBEDDING_MODE) are now set automatically by Terraform. The OpenAI Lambda layer is also created and attached automatically.

### 7. Run Local API

```powershell
# From project root
.\scripts\run_local_api.ps1
```

API will be available at `http://localhost:8000`

### 8. Manual Testing Workflow

#### 8.1 Get Presigned URL

```powershell
$body = @{
    filename = "test.txt"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/presign" `
    -Method POST -Body $body -ContentType "application/json"

$traceId = $response.trace_id
$uploadUrl = $response.url
$s3Key = $response.key

Write-Host "Trace ID: $traceId"
Write-Host "S3 Key: $s3Key"
```

#### 8.2 Upload File to S3

```powershell
$content = "This is a test document about machine learning and artificial intelligence. Machine learning is a subset of artificial intelligence that enables systems to learn from data."

Invoke-RestMethod -Uri $uploadUrl -Method PUT -Body $content -ContentType "text/plain"
```

#### 8.3 Wait for Processing

- Check CloudWatch logs for Lambda function
- Or wait ~30-60 seconds for SQS → Lambda processing

#### 8.4 Query Knowledge Base

```powershell
$body = @{
    question = "What is machine learning?"
    top_k = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/ask" `
    -Method POST -Body $body -ContentType "application/json"
```

### 9. Run Tests

```powershell
.\scripts\test.ps1
```

### 10. Format Code

```powershell
.\scripts\fmt.ps1
```

## Troubleshooting

### Lambda Not Processing

1. Check CloudWatch logs: `/aws/lambda/proof-layer-processor`
2. Verify Lambda environment variables are set
3. Check SQS queue for messages
4. Verify S3 event notification is configured

### Database Connection Issues

1. Verify Supabase connection string format
2. Check service role key is correct
3. Ensure pgvector extension is enabled
4. Test connection manually with psql

### No Results from /ask

1. Verify documents were processed (check `documents` table)
2. Check `chunks` table has data with embeddings
3. Verify similarity threshold isn't too high
4. Check trace_id propagation in logs

## Next Steps

- Monitor CloudWatch logs for errors
- Set up log retention policies
- Consider adding IVFFlat index after data load (see migration comments)
- Switch to real embeddings (OpenAI) if needed

