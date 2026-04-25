from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.media_asset import MediaAsset
from app.services.s3_service import generate_put_presigned_url


router = APIRouter(prefix="/media")

ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "image/jpeg",
    "image/png",
    "application/x-subrip",
    "text/plain",
}

VIDEO_LIMIT = 500 * 1024 * 1024
IMAGE_LIMIT = 20 * 1024 * 1024
SUBTITLE_LIMIT = 5 * 1024 * 1024


class PresignRequest(BaseModel):
    filename: str
    mimeType: str
    size: int


class CompleteRequest(BaseModel):
    assetId: int
    objectKey: str


class MultipartInitRequest(BaseModel):
    filename: str
    mimeType: str
    size: int


class MultipartPartRequest(BaseModel):
    uploadId: str
    objectKey: str
    partNumber: int


class MultipartCompleteRequest(BaseModel):
    uploadId: str
    objectKey: str
    parts: list[dict] = []


class MultipartAbortRequest(BaseModel):
    uploadId: str
    objectKey: str


def detect_file_type(mime_type: str) -> str:
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("image/"):
        return "image"
    return "subtitle"


def validate_upload(payload: PresignRequest) -> str:
    # 后端再次校验文件类型和大小，避免绕过前端限制。
    if payload.mimeType not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    file_type = detect_file_type(payload.mimeType)
    if file_type == "video" and payload.size > VIDEO_LIMIT:
        raise HTTPException(status_code=400, detail="视频文件不能超过 500MB")
    if file_type == "image" and payload.size > IMAGE_LIMIT:
        raise HTTPException(status_code=400, detail="图片文件不能超过 20MB")
    if file_type == "subtitle" and payload.size > SUBTITLE_LIMIT:
        raise HTTPException(status_code=400, detail="字幕文件不能超过 5MB")
    return file_type


def asset_to_dict(asset: MediaAsset) -> dict:
    return {
        "id": asset.id,
        "filename": asset.filename,
        "originalFilename": asset.original_filename,
        "fileType": asset.file_type,
        "mimeType": asset.mime_type,
        "size": asset.size,
        "objectKey": asset.object_key,
        "url": asset.url,
        "provider": asset.provider,
        "status": asset.status,
        "createdAt": asset.created_at.isoformat(),
    }


@router.post("/presign")
def presign_upload(payload: PresignRequest, db: Session = Depends(get_db)):
    file_type = validate_upload(payload)
    try:
        presign = generate_put_presigned_url(payload.filename, payload.mimeType)
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=500, detail="缺少 boto3 依赖，请在 backend 执行 pip install -r requirements.txt") from exc
    except Exception as exc:
        # 签名失败通常来自 endpoint、bucket、密钥权限或 region 配置错误。
        raise HTTPException(status_code=500, detail=f"S3 签名失败：{exc}") from exc

    asset = MediaAsset(
        filename=Path(presign["objectKey"]).name,
        original_filename=payload.filename,
        file_type=file_type,
        mime_type=payload.mimeType,
        size=payload.size,
        object_key=presign["objectKey"],
        url=presign["publicUrl"],
        provider=presign["provider"],
        status="pending",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "assetId": asset.id,
            "uploadUrl": presign["uploadUrl"],
            "objectKey": presign["objectKey"],
            "publicUrl": presign["publicUrl"],
            "provider": presign["provider"],
        },
    }


@router.post("/complete")
def complete_upload(payload: CompleteRequest, db: Session = Depends(get_db)):
    asset = db.query(MediaAsset).filter(MediaAsset.id == payload.assetId).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    if asset.object_key != payload.objectKey:
        raise HTTPException(status_code=400, detail="objectKey 不匹配")

    asset.status = "uploaded"
    db.commit()
    db.refresh(asset)
    return {"code": 0, "message": "success", "data": asset_to_dict(asset)}


@router.get("/assets")
def list_assets(db: Session = Depends(get_db)):
    assets = db.query(MediaAsset).order_by(MediaAsset.created_at.desc()).limit(50).all()
    return {"code": 0, "message": "success", "data": [asset_to_dict(asset) for asset in assets]}


@router.get("/assets/{asset_id}")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    return {"code": 0, "message": "success", "data": asset_to_dict(asset)}


@router.post("/multipart/init")
def multipart_init(_: MultipartInitRequest):
    # 预留大文件分片上传入口，后续可接 S3 create_multipart_upload。
    return {"code": 0, "message": "success", "data": {"todo": "multipart upload init reserved"}}


@router.post("/multipart/presign-part")
def multipart_presign_part(_: MultipartPartRequest):
    # 预留单个分片签名入口，后续可按 partNumber 生成 upload_part presigned URL。
    return {"code": 0, "message": "success", "data": {"todo": "multipart upload part presign reserved"}}


@router.post("/multipart/complete")
def multipart_complete(_: MultipartCompleteRequest):
    # 预留分片合并入口，后续可接 S3 complete_multipart_upload。
    return {"code": 0, "message": "success", "data": {"todo": "multipart upload complete reserved"}}


@router.post("/multipart/abort")
def multipart_abort(_: MultipartAbortRequest):
    # 预留分片取消入口，后续可接 S3 abort_multipart_upload。
    return {"code": 0, "message": "success", "data": {"todo": "multipart upload abort reserved"}}
