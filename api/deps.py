"""FastAPI dependencies."""

import os
from functools import lru_cache

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()


def _validate_aws_credentials():
    """Validate AWS credentials are present and not placeholders.
    
    Checks both environment variables and boto3's credential chain.
    Fails fast with clear error if credentials are missing or contain placeholders.
    """
    placeholder_values = [
        "your_access_key_here",
        "your_secret_key_here",
        "YOUR_ACCESS_KEY_HERE",
        "YOUR_SECRET_KEY_HERE",
    ]
    
    # Check environment variables for placeholders
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if access_key and access_key in placeholder_values:
        raise ValueError(
            "AWS_ACCESS_KEY_ID contains placeholder value. "
            "Please set valid AWS credentials via environment variables or ~/.aws/credentials"
        )
    
    if secret_key and secret_key in placeholder_values:
        raise ValueError(
            "AWS_SECRET_ACCESS_KEY contains placeholder value. "
            "Please set valid AWS credentials via environment variables or ~/.aws/credentials"
        )
    
    # Validate credentials from boto3's credential chain
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            raise ValueError(
                "AWS credentials not found. "
                "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables, "
                "or configure ~/.aws/credentials file"
            )
        
        # Check if resolved credentials are placeholders
        access_key_id = credentials.access_key
        if access_key_id in placeholder_values:
            raise ValueError(
                "AWS credentials contain placeholder values. "
                "Please set valid AWS credentials via environment variables or ~/.aws/credentials"
            )
        
    except NoCredentialsError:
        raise ValueError(
            "AWS credentials not found. "
            "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables, "
            "or configure ~/.aws/credentials file"
        )


def _get_aws_region() -> str:
    """Get AWS region from environment variables, default to us-east-1."""
    # Check AWS_REGION first, then AWS_DEFAULT_REGION, then default
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    return region


@lru_cache()
def get_s3_client():
    """Get S3 client using boto3 default credential chain with SigV4.
    
    Uses boto3's default credential chain (env vars, ~/.aws/credentials, IAM role, etc.).
    Validates credentials are present and not placeholders.
    Fails fast with clear error message if credentials are missing or invalid.
    Creates client with explicit region to ensure SigV4 presigning.
    """
    # Validate credentials before creating client
    _validate_aws_credentials()
    
    # Get AWS region from environment (AWS_REGION or AWS_DEFAULT_REGION), default to us-east-1
    region = _get_aws_region()
    
    # Use boto3 default credential chain - do not pass credentials explicitly
    # This allows boto3 to pick up creds from env vars, ~/.aws/credentials, or IAM role
    # Explicitly set region_name to ensure SigV4 presigning
    try:
        client = boto3.client(
            "s3",
            region_name=region,
        )
        return client
    except NoCredentialsError as e:
        raise ValueError(
            "AWS credentials not found. "
            "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables, "
            "or configure ~/.aws/credentials file"
        ) from e
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "InvalidAccessKeyId":
            raise ValueError(
                "Invalid AWS credentials detected. "
                "Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. "
                "Ensure they are not placeholder values."
            ) from e
        raise


@lru_cache()
def get_s3_bucket():
    """Get S3 bucket name from env."""
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise ValueError("S3_BUCKET_NAME environment variable is required")
    return bucket


def validate_region_consistency():
    """Validate that region matches expected us-east-1 for this stack."""
    region = _get_aws_region()
    expected_region = "us-east-1"
    
    if region != expected_region:
        raise ValueError(
            f"Region mismatch: AWS_REGION/AWS_DEFAULT_REGION is set to '{region}', "
            f"but this stack expects '{expected_region}'. "
            f"Please set AWS_REGION={expected_region} or AWS_DEFAULT_REGION={expected_region}"
        )

