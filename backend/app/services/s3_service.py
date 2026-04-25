from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_S3_BUCKET,
    AWS_S3_ENDPOINT_URL,
    AWS_S3_PUBLIC_BASE_URL,
    AWS_SECRET_ACCESS_KEY,
    MEDIA_PROVIDER,
    S3_ADDRESSING_STYLE,
    S3_PRESIGNED_EXPIRE_SECONDS,
    S3_SIGNATURE_VERSION,
    S3_UPLOAD_PREFIX,
)


def is_s3_enabled() -> bool:
    # 只有 provider 和关键 S3 配置都存在时才启用真实上传。
    return (
        MEDIA_PROVIDER == "s3"
        and bool(AWS_ACCESS_KEY_ID)
        and bool(AWS_SECRET_ACCESS_KEY)
        and bool(AWS_S3_BUCKET)
    )


def create_s3_client():
    # boto3 只在真实 S3 模式下创建客户端，避免 mock 演示依赖 AWS 配置。
    import boto3
    from botocore.config import Config

    client_kwargs = {
        "service_name": "s3",
        "region_name": AWS_REGION,
        "aws_access_key_id": AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
        "config": Config(
            signature_version=S3_SIGNATURE_VERSION,
            s3={"addressing_style": S3_ADDRESSING_STYLE},
        ),
    }

    # S3 兼容服务需要指定自定义 endpoint，例如 https://s3.hi168.com。
    if AWS_S3_ENDPOINT_URL:
        client_kwargs["endpoint_url"] = AWS_S3_ENDPOINT_URL.rstrip("/")

    return boto3.client(**client_kwargs)


def build_object_key(filename: str) -> str:
    # 对象路径按日期分组，文件名前加 UUID，避免重名覆盖。
    safe_name = Path(filename).name.replace(" ", "_")
    date_part = datetime.now().strftime("%Y%m%d")
    return f"{S3_UPLOAD_PREFIX}/{date_part}/{uuid4().hex}_{safe_name}"


def build_public_url(object_key: str) -> str:
    # public base 可配置为 S3 域名、S3 兼容服务地址或 CloudFront 域名。
    if AWS_S3_PUBLIC_BASE_URL:
        return f"{AWS_S3_PUBLIC_BASE_URL.rstrip('/')}/{object_key}"
    if AWS_S3_ENDPOINT_URL and AWS_S3_BUCKET:
        return f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_S3_BUCKET}/{object_key}"
    if AWS_S3_BUCKET:
        return f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
    return f"mock://{object_key}"


def generate_put_presigned_url(filename: str, content_type: str) -> dict:
    object_key = build_object_key(filename)
    public_url = build_public_url(object_key)

    if not is_s3_enabled():
        # mock 模式返回占位 URL，前端会模拟上传进度并完成元数据保存。
        return {
            "uploadUrl": f"mock://upload/{object_key}",
            "objectKey": object_key,
            "publicUrl": public_url,
            "provider": "mock",
        }

    s3 = create_s3_client()
    upload_url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": AWS_S3_BUCKET,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=S3_PRESIGNED_EXPIRE_SECONDS,
        HttpMethod="PUT",
    )

    return {
        "uploadUrl": upload_url,
        "objectKey": object_key,
        "publicUrl": public_url,
        "provider": "s3",
    }
