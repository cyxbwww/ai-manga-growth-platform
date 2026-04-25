from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def health_check():
    # 健康检查接口：用于验证后端服务和 API 前缀是否正常。
    return {
        "code": 0,
        "message": "success",
        "data": "ok",
    }
