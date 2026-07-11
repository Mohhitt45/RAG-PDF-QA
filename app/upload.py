import os
import shutil

from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from app.config import (
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    UPLOAD_FOLDER,
    VECTORSTORE_FOLDER,
    ALLOWED_EXTENSION
)



def upload_pdf(file: UploadFile):

    # Validate PDF
    if not file.filename.endswith(ALLOWED_EXTENSION):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    pdf_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    # Save uploaded PDF
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Split text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(documents)

    for chunk in chunks:
        chunk.metadata["source"] = file.filename

    # Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    # Create FAISS
    #import os

    faiss_index = os.path.join(VECTORSTORE_FOLDER, "index.faiss")

    if os.path.exists(faiss_index):


        vectorstore = FAISS.load_local(
            VECTORSTORE_FOLDER,
            embeddings,
            allow_dangerous_deserialization=True
        )

        vectorstore.add_documents(chunks)

    else:

        vectorstore = FAISS.from_documents(
            chunks,
            embeddings
        )

    vectorstore.save_local(VECTORSTORE_FOLDER)

    return {
        "message": "PDF uploaded successfully.",
        "filename": file.filename,
        "chunks": len(chunks)
    }