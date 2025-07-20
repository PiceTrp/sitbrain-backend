from fastapi import APIRouter

from app.api.v1.routes import chat, document

api_router = APIRouter()
api_router.include_router(document.router, prefix="/v1", tags=["v1"])
api_router.include_router(chat.router, prefix="/v1", tags=["v1"])
