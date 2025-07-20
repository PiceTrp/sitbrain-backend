import asyncio
from typing import List

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingService:
    """
    * embedding generation service
    """

    def __init__(self):
        self.client = genai.Client()
        self.model = settings.embedding_model  # model name

    def generate_embedding(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        * generate embedding for single text
        """
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return response.embeddings[0].values

    def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 8,
    ) -> List[List[float]]:
        """
        * generate embeddings for multiple texts
        """
        # * process in batches to avoid rate limits
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            response = self.client.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )

            batch_embeddings = [embedding.values for embedding in response.embeddings]
            all_embeddings.extend(batch_embeddings)

            # * small delay between batches
            if i + batch_size < len(texts):
                asyncio.sleep(0.1)

        return all_embeddings


# def main():
#     service = EmbeddingService()

#     # Example input texts
#     text_single = "This is a test sentence for embedding."
#     texts_batch = ["Machine learning is amazing."] * 8 + ["ChatGPT helps you write code."] * 14

#     # Test single embedding generation
#     print("Generating embedding for a single text...")
#     single_embedding = service.generate_embedding(text_single)
#     print(f"Single embedding {single_embedding.embeddings[0].values}")  # show first 5 dims

#     # Test batch embedding generation
#     print("\nGenerating embeddings for a batch of texts...")
#     batch_embeddings = service.generate_embeddings_batch(texts_batch)
#     print(len(batch_embeddings))
#     for i, emb in enumerate(batch_embeddings):
#         print(f"Text {i+1} embedding (length={len(emb)}): {emb[:5]}...")  # show first 5 dims

# if __name__ == "__main__":
#     main()
