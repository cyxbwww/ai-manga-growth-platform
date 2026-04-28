from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.media_asset import MediaAsset
from app.models.short_drama_episode import ShortDramaEpisode
from app.services.project_flow import advance_project_stage
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
    project_id: Optional[int] = None
    episode_id: Optional[int] = None
    episode_no: Optional[int] = None


class CompleteRequest(BaseModel):
    assetId: int
    objectKey: str
    project_id: Optional[int] = None
    episode_id: Optional[int] = None
    episode_no: Optional[int] = None


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
        "project_id": asset.project_id,
        "episode_id": asset.episode_id,
        "episode_no": asset.episode_no,
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
        project_id=payload.project_id,
        episode_id=payload.episode_id,
        episode_no=payload.episode_no,
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
            "project_id": asset.project_id,
            "episode_id": asset.episode_id,
            "episode_no": asset.episode_no,
        },
    }


@router.post("/complete")
def complete_upload(payload: CompleteRequest, db: Session = Depends(get_db)):
    asset = db.query(MediaAsset).filter(MediaAsset.id == payload.assetId).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    if asset.object_key != payload.objectKey:
        raise HTTPException(status_code=400, detail="objectKey 不匹配")

    if payload.project_id and not asset.project_id:
        # complete 阶段允许补写 project_id，兼容 presign 阶段未绑定项目的旧流程。
        asset.project_id = payload.project_id
    if payload.episode_id and not asset.episode_id:
        # complete 阶段允许补写 episode 信息，兼容 presign 阶段未绑定分集的旧流程。
        asset.episode_id = payload.episode_id
    if payload.episode_no and not asset.episode_no:
        asset.episode_no = payload.episode_no
    asset.status = "uploaded"
    db.commit()
    db.refresh(asset)
    # 媒体上传属于素材制作资产沉淀，完成后保持项目在 material 阶段，后续广告素材生成再推进到 launch。
    advance_project_stage(db, asset.project_id or payload.project_id, "material")
    if asset.episode_id or payload.episode_id:
        try:
            episode = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.id == (asset.episode_id or payload.episode_id)).first()
            if episode:
                # 分集级媒体资产状态流转：图片/字幕仍处于媒体制作，视频素材通常代表成片或镜头素材已具备，可推进为 completed。
                episode.media_status = "completed"
                episode.stage = "completed" if asset.file_type == "video" else "media"
                episode.updated_at = datetime.now()
                db.commit()
        except Exception as exc:
            db.rollback()
            print(f"媒体上传完成后更新分集状态失败，已忽略：episode_id={asset.episode_id or payload.episode_id}, error={exc}")
    return {"code": 0, "message": "success", "data": asset_to_dict(asset)}


@router.get("/assets")
def list_assets(
    project_id: Optional[int] = Query(default=None),
    episode_id: Optional[int] = Query(default=None),
    episode_no: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(MediaAsset)
    if project_id:
        query = query.filter(MediaAsset.project_id == project_id)
    if episode_id:
        query = query.filter(MediaAsset.episode_id == episode_id)
    if episode_no:
        query = query.filter(MediaAsset.episode_no == episode_no)
    assets = query.order_by(MediaAsset.created_at.desc()).limit(50).all()
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
