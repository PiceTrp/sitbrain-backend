import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.services.embeddings_service import EmbeddingService
from app.utils.logger import LOGGER


class QdrantVectorStore:
    def __init__(self, embedding_service: EmbeddingService):
        # * qdrant client configuration
        self.client = QdrantClient(
            url=settings.qdrant_url,
        )
        self.collection_name = settings.qdrant_collection_name

        # * embedding model
        self.embedding_service = embedding_service
        self.vector_size = settings.embedding_size

        # * create collection if not exists
        self._create_collection()

    def _create_collection(self):
        """create qdrant collection"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE
                ),
            )

    def upsert_point(
        self, embedding: List[float], payload: Dict[str, Any] = None
    ) -> str:
        """Add a single document to vector store"""
        point_id = str(uuid.uuid4())
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload,
        )

        try:
            LOGGER.info(f"[Upsert] Inserting 1 point with id={point_id}")
            self.client.upsert(collection_name=self.collection_name, points=[point])
            return point_id
        except Exception as e:
            LOGGER.exception(
                f"[Error] Failed to upsert point with id={point_id}: {str(e)}"
            )
            raise

    def upsert_points(
        self, embeddings: List[List[float]], payloads: List[Dict[str, Any]] = None
    ):
        """Add multiple documents to vector store"""
        points = []

        try:
            for i, embedding in enumerate(embeddings):
                point_id = str(uuid.uuid4())
                payload = payloads[i] if payloads else None
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
                points.append(point)
                LOGGER.debug(
                    f"[Upsert] Prepared point {i} with id={point_id}, payload_keys={list(payload.keys()) if payload else 'None'}"
                )

            LOGGER.info(
                f"[Upsert] Inserting {len(points)} points into collection: {self.collection_name}"
            )
            self.client.upsert(collection_name=self.collection_name, points=points)

        except Exception as e:
            LOGGER.exception(f"[Error] Failed to upsert multiple points: {str(e)}")
            raise

    def update_document(
        self, doc_id: int, content: str, metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """update document in vector store"""
        # * delete existing points for this document
        self.delete_document(doc_id)
        # * add new point
        return self.add_document(doc_id, content, metadata)

    def delete_document(self, doc_id: int) -> bool:
        """delete document from vector store"""
        try:
            # * search for points with this doc_id
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "doc_id", "match": {"value": doc_id}}]},
                limit=1000,
            )

            # * delete all points
            if search_result[0]:
                point_ids = [point.id for point in search_result[0]]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector={"points": point_ids},
                )

            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def delete_collection(self, collection_name: str = "demo_collection") -> None:
        """delete collection from vector store"""
        self.client.delete_collection(
            collection_name=collection_name,
        )

    def retrieve_contexts(self, query: str, top_k: int = 5) -> List[Dict]:
        """retrieve contexts from vector store -- (retrieved points from qdrant)"""
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=self.embedding_service.generate_embedding(
                text=query, task_type="retrieval_query"
            ),
            limit=top_k,
        )
        retrieved_results = [dict(item) for item in hits.points]
        return retrieved_results
