from fastapi import APIRouter, HTTPException

from app.services.dictionary_service import get_all_dictionaries, get_dictionary


router = APIRouter(prefix="/dictionaries")


@router.get("")
def list_dictionaries():
    # 统一返回全部业务字典，前端可一次加载并缓存，避免各页面写死选项。
    return {
        "code": 0,
        "message": "success",
        "data": get_all_dictionaries(),
    }


@router.get("/{dict_type}")
def get_dictionary_by_type(dict_type: str):
    dictionary = get_dictionary(dict_type)
    if dictionary is None:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    return {
        "code": 0,
        "message": "success",
        "data": dictionary,
    }
