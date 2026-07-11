from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

from app.config import (
    EMBEDDING_MODEL,
    LLM_MODEL,
    TOP_K
)

# Load embedding model
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)

# Load FAISS database
vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

# Create retriever
retriever = vectorstore.as_retriever(
    search_kwargs={"k": TOP_K}
)

# Load Local LLM
llm = OllamaLLM(
    model=LLM_MODEL
)

# Prompt Template
prompt = PromptTemplate(
    template="""
You are an AI assistant.

Answer ONLY from the given context.
If the answer is not present in the context, reply:
"I could not find the answer in the provided document."

Context:
{context}

Question:
{question}

Answer:
""",
    input_variables=["context", "question"]
)


def ask_question(question: str):

    # Retrieve relevant chunks
    docs = retriever.invoke(question)

    # Combine retrieved chunks
    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    # Generate answer
    response = llm.invoke(
        prompt.format(
            context=context,
            question=question
        )
    )

    # Collect source information
    sources = []

    for doc in docs:
        sources.append({
            "file": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 0) + 1,
            "content": doc.page_content[:200]
        })

    # Return answer + sources
    return {
        "answer": response,
        "sources": sources
    }