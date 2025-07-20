from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1.main import api_router
from app.core.service_manager import service_manager
from app.utils.logger import LOGGER


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    * application lifespan manager - startup and shutdown
    """
    # * startup
    try:
        LOGGER.info("starting application...")
        await service_manager.initialize()
        LOGGER.info("application startup completed")
    except Exception as e:
        LOGGER.error(f"application startup failed: {e}")
        raise

    yield

    # * shutdown
    try:
        LOGGER.info("shutting down application...")
        await service_manager.shutdown()
        LOGGER.info("application shutdown completed")
    except Exception as e:
        LOGGER.error(f"application startup failed: {e}")


# * initialize fastapi app
app = FastAPI(
    title="RAG Chat API",
    version="1.0.0",
    description="A FastAPI-based RAG service with PostgreSQL and Qdrant",
    lifespan=lifespan,  # initialize services first running up
)


# * default endpoint
@app.get("/")
async def root():
    return {"message": "RAG Chat API", "version": "1.0.0", "status": "running"}


# * health check endpoint
@app.get("/health")
async def health_check():
    try:
        # * check if services are initialized
        vector_store = service_manager.get_vector_store()
        embedding_service = service_manager.get_embedding_service()
        llm_service = service_manager.get_llm_service()

        # check
        if not vector_store or not embedding_service or not llm_service:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "services not initialized",
                },
            )

        return {
            "status": "healthy",
            "services": {
                "vector_store": "ok",
                "embedding_service": "ok",
                "llm_service": "ok",
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "error": str(e)}
        )


app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
