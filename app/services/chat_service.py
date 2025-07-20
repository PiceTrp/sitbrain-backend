import json
import time
from typing import Dict, List

from app.core.prompts import rag_prompt_template
from app.core.service_manager import service_manager
from app.schemas.chat import ChatResponse


class ChatService:
    """
    * basic rag chat service
    """

    def __init__(self):
        self.llm_model = service_manager.get_llm_service().get_chat_model()
        self.vector_store = service_manager.get_vector_store()

    def process_question(self, question: str, top_k: int = 5) -> ChatResponse:
        """
        * process user question with rag pipeline
        """
        start_time = time.time()

        # * step 1: Retrieval
        retrieved_results = self.vector_store.retrieve_contexts(
            query=question, top_k=top_k
        )

        # * step 2: Augmented - prepare context in llm-ready (strinified json)
        context = self._prepare_context_with_sources(retrieved_results)

        # * step 3: Generation
        answer = self._generate_answer(question, context)
        mock_sources = ["aaa.pdf", "bbb.pdf"]

        processing_time = time.time() - start_time

        return ChatResponse(
            answer=answer, sources=mock_sources, processing_time=processing_time
        )

    def _prepare_context_with_sources(self, retrieved_results: List[Dict]) -> str:
        """
        * prepare context string and integrate source references in the context
        """
        # convert to only necessary chunk info
        response_list = []
        for retrieved_chunk in retrieved_results:
            data_dict = {}
            data_dict["vector_id"] = retrieved_chunk["id"]
            data_dict["relevance_score"] = retrieved_chunk["score"]
            data_dict["content"] = retrieved_chunk["payload"]["document"]
            data_dict["filename"] = retrieved_chunk["payload"]["filename"]
            data_dict["page_number"] = retrieved_chunk["payload"]["page_number"]
            response_list.append(data_dict)

        # convert to string as context input to prompt template
        contexts = json.dumps(response_list, ensure_ascii=False, indent=4)

        return contexts

    def _generate_answer(self, question: str, context: str) -> str:
        """
        * generate answer using llm
        """
        messages = rag_prompt_template.format(context=context, question=question)
        response = self.llm_model.invoke(messages)
        return response.content


# f"""Answer the following question based on the provided context.

# If you reference information from the context, include the source number in your answer like [Source 1], [Source 2], etc.

# Context:
# {context}

# Question: {question}

# Answer:"""
