from fastapi import APIRouter, HTTPException
from app.data_loader import HERITAGE, find_heritage, search_heritage

router = APIRouter(prefix="/heritage", tags=["heritage"])


@router.get("")
def list_heritage(q: str = ""):
    return search_heritage(q)


@router.get("/{name}")
def heritage_detail(name: str):
    item = find_heritage(name)
    if not item:
        raise HTTPException(404, "Heritage site not found")
    return item
