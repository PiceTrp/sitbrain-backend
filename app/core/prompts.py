from langchain.prompts import PromptTemplate

rag_prompt_template = PromptTemplate.from_template(
    """
You will be provided with a context in JSON format, consisting of a list of documents retrieved based on relevance scores. Please answer the following question **in Thai language** by strictly following the instructions below:

### Instructions:
1. **Answer comprehensively and clearly** using only the information available in the provided context.
2. **If the context does not contain enough information** to fully answer the question, explicitly state what information is missing.
3. **Do not use any external knowledge** or assumptions outside of the given context.
4. **Be specific and detailed** in your answer based on the available data.
5. **At the end of your answer**, include a list of all referenced sources by specifying the `filename` and `page_number` fields from the context.

### Context:
{context}

### Question:
{question}

### Answer (in Thai):
"""
)

# if __name__ == '__main__':
#     print(rag_prompt_template.format(context="context", question="question"))
