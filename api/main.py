"""FastAPI main application."""

import json
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.deps import get_s3_bucket, get_s3_client, validate_region_consistency
from api.models import AskRequest, AskResponse, PresignRequest, PresignResponse
from api.rag import answer_question
from api.utils import build_s3_key, generate_trace_id

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Validate region consistency and log configuration on startup
try:
    validate_region_consistency()
    bucket = get_s3_bucket()
    # Get region from env for logging (same logic as deps)
    import os
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    logger.info(f"S3 configuration: region={region}, bucket={bucket}")
except Exception as e:
    logger.error(f"Startup validation failed: {e}")
    raise

app = FastAPI(
    title="AWS Proof Layer API",
    description="RAG pipeline API with S3, SQS, Lambda, and Supabase",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"ok": True}


@app.post("/presign", response_model=PresignResponse)
async def presign(request: PresignRequest):
    """Generate presigned S3 URL for file upload."""
    try:
        trace_id = generate_trace_id()
        bucket = get_s3_bucket()
        key = build_s3_key(trace_id, request.filename)
        
        s3_client = get_s3_client()
        
        # Generate presigned URL (valid for 1 hour)
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": "text/plain",
            },
            ExpiresIn=3600,
        )
        
        logger.info(
            json.dumps({
                "event": "presign_created",
                "trace_id": trace_id,
                "bucket": bucket,
                "key": key,
            })
        )
        
        return PresignResponse(
            trace_id=trace_id,
            bucket=bucket,
            key=key,
            url=url,
        )
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Answer a question using RAG."""
    try:
        result = answer_question(request.question, request.top_k)
        
        logger.info(
            json.dumps({
                "event": "ask_query",
                "trace_id": result["trace_id"],
                "question": request.question,
                "refused": result["refused"],
                "citations_count": len(result["citations"]),
            })
        )
        
        return AskResponse(**result)
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)

