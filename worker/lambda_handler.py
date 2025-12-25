"""Lambda handler for SQS-triggered document processing."""

import json
import logging
import os

from .ingest import ingest_document
from .utils import log_structured

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """
    Lambda handler for SQS events.
    
    Expected event structure:
    {
        "Records": [
            {
                "body": "{\"Records\": [{\"s3\": {\"bucket\": {\"name\": \"...\"}, \"object\": {\"key\": \"...\"}}}]}"
            }
        ]
    }
    """
    # Process each SQS record
    for record in event.get("Records", []):
        try:
            # Parse SQS message body (which contains S3 event)
            body = json.loads(record["body"])
            
            # Extract S3 event records
            s3_records = body.get("Records", [])
            
            for s3_record in s3_records:
                # Extract bucket and key from S3 event
                s3_data = s3_record.get("s3", {})
                bucket = s3_data.get("bucket", {}).get("name")
                key = s3_data.get("object", {}).get("key")
                
                # URL decode the key
                if key:
                    import urllib.parse
                    key = urllib.parse.unquote_plus(key)
                
                if not bucket or not key:
                    logger.warning(f"Missing bucket or key in S3 event: {s3_record}")
                    continue
                
                # Ingest the document
                ingest_document(bucket, key)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SQS message body: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing record: {e}", exc_info=True)
            # Re-raise to trigger DLQ
            raise
    
    return {"statusCode": 200, "body": json.dumps("Processing completed")}

