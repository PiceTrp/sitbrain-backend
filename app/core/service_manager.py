from typing import Optional

from app.services.embeddings_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.qdrant_vector_store import QdrantVectorStore
from app.utils.logger import LOGGER


class ServiceManager:
    """
    * centralized service manager for application-wide service instances
    """

    _instance: Optional["ServiceManager"] = None
    _initialized: bool = False

    def __init__(self):
        self.embedding_service: Optional[EmbeddingService] = None
        self.llm_service: Optional[LLMService] = None
        self.vector_store: Optional[QdrantVectorStore] = None

    @classmethod
    def get_instance(cls) -> "ServiceManager":
        """
        * get singleton instance of service manager
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self):
        """
        * initialize all services
        """
        if self._initialized:
            LOGGER.info("services already initialized")
            return

        try:
            LOGGER.info("initializing application services...")

            # * initialize embedding service
            LOGGER.info("initializing embedding service...")
            self.embedding_service = EmbeddingService()

            # * initialize llm service
            LOGGER.info("initializing llm service...")
            self.llm_service = LLMService()

            # * initialize qdrant vector store
            LOGGER.info("initializing qdrant vector store...")
            self.vector_store = QdrantVectorStore(
                embedding_service=self.embedding_service
            )

            # * warm up services
            await self._warmup_services()

            self._initialized = True
            LOGGER.info("all services initialized successfully")

        except Exception as e:
            LOGGER.error(f"failed to initialize services: {str(e)}")
            raise

    async def _warmup_services(self):
        """
        * warm up services to avoid cold start delays
        """
        try:
            LOGGER.info("warming up services...")

            # * warm up embedding service
            if self.embedding_service:
                self.embedding_service.generate_embedding(
                    "warmup test", task_type="retrieval_query"
                )

            # * warm up llm service
            # if self.llm_service:
            #     test = self.llm_service.chat_model.invoke("warmup test")

            # * warm up vector store connection
            if self.vector_store:
                # * test connection by checking collection
                try:
                    self.vector_store.client.get_collection(
                        self.vector_store.collection_name
                    )
                except Exception:
                    # * collection might not exist yet, that's ok
                    pass

            LOGGER.info("service warmup completed")

        except Exception as e:
            LOGGER.warning("service warmup failed", error=str(e))
            # * don't fail initialization if warmup fails

    def get_vector_store(self) -> QdrantVectorStore:
        """
        * get vector store instance
        """
        if not self._initialized or self.vector_store is None:
            raise RuntimeError("vector store not initialized - call initialize() first")
        return self.vector_store

    def get_embedding_service(self) -> EmbeddingService:
        """
        * get embedding service instance
        """
        if not self._initialized or self.embedding_service is None:
            raise RuntimeError(
                "embedding service not initialized - call initialize() first"
            )
        return self.embedding_service

    def get_llm_service(self) -> LLMService:
        """
        * get llm service instance
        """
        if not self._initialized or self.llm_service is None:
            raise RuntimeError("llm service not initialized - call initialize() first")
        return self.llm_service

    async def shutdown(self):
        """
        * cleanup services on shutdown
        """
        try:
            LOGGER.info("shutting down services...")

            # * add cleanup logic here
            if self.vector_store:
                # * close vector store connections if needed
                pass

            if self.embedding_service:
                # * cleanup embedding service if needed
                pass

            self._initialized = False
            LOGGER.info("services shutdown completed")

        except Exception as e:
            LOGGER.error(f"error during service shutdown: {str(e)}")


# * global service manager instance
service_manager = ServiceManager.get_instance()
