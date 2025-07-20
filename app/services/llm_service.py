from langchain.chat_models import init_chat_model

from app.core.config import settings
from app.utils.logger import LOGGER


class LLMService:
    """
    * llm service for chat model initialization
    """

    def __init__(self):
        """
        * initialize chat model
        """
        try:
            LOGGER.info("initializing llm chat model...")
            self.chat_model = init_chat_model(
                model=settings.chat_model, model_provider="google_genai"
            )
            LOGGER.info("llm chat model initialized successfully")
        except Exception as e:
            LOGGER.error(f"failed to initialize llm chat model: {str(e)}")
            raise

    def get_chat_model(self):
        """
        * get initialized chat model
        """
        if self.chat_model is None:
            self.__init__()
        return self.chat_model
