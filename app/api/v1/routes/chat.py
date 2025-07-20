import traceback

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


# * dependency injection using service manager
def get_chat_service() -> ChatService:
    """
    * get initialized chat service from service manager
    """
    return ChatService()  # * ChatService now uses service_manager internally


@router.post("/", response_model=ChatResponse)
def rag_endpoint(
    request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)
):
    """
    * process user question with rag pipeline
    """
    try:
        response = chat_service.process_question(
            question=request.question,
            top_k=settings.top_k_results,
        )
        return response
    except Exception:
        # in development only, do not do this in production
        tb_str = traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(tb_str))
