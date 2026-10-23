
import os
from io import BytesIO
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pypdf import PdfReader

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq


# Load environment variables from .env
load_dotenv()


# -----------------------------------------
# 1. Load PDF, TXT, or default document
# -----------------------------------------

def load_document(file_name=None, file_bytes=None):

    # Load the default sample document
    if file_bytes is None:
        document_path = Path("documents") / "rag_notes.txt"

        if not document_path.exists():
            raise FileNotFoundError(
                "Default document not found: documents/rag_notes.txt"
            )

        text = document_path.read_text(encoding="utf-8")

        if not text.strip():
            raise ValueError("The default document is empty.")

        return [
            Document(
                page_content=text,
                metadata={
                    "source": str(document_path),
                    "page": None
                }
            )
        ]

    extension = Path(file_name).suffix.lower()
    documents = []

    # Read PDF one page at a time
    if extension == ".pdf":

        reader = PdfReader(BytesIO(file_bytes))

        for page_number, page in enumerate(reader.pages, start=1):

            page_text = page.extract_text() or ""

            if page_text.strip():
                documents.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "source": file_name,
                            "page": page_number
                        }
                    )
                )

    # Read TXT document
    elif extension == ".txt":

        text = file_bytes.decode(
            "utf-8-sig",
            errors="replace"
        )

        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": file_name,
                        "page": None
                    }
                )
            )

    else:
        raise ValueError("Please upload a PDF or TXT file.")

    if not documents:
        raise ValueError(
            "No readable text was found in this document. "
            "Scanned PDFs may require OCR."
        )

    return documents


# -----------------------------------------
# 2. Create the embedding model
# -----------------------------------------

@lru_cache(maxsize=1)
def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# -----------------------------------------
# 3. Initialize Groq LLM
# -----------------------------------------

@lru_cache(maxsize=1)
def get_llm():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key
    )


# -----------------------------------------
# 4. Create the Chroma vector database
# -----------------------------------------

def create_vector_store(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No text chunks could be created.")

    # Page metadata is preserved when documents are split.
    embeddings = get_embeddings()

    # Replace the previous collection to avoid mixing
    # chunks from different documents.
    old_db = Chroma(
        collection_name="documentation",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    old_db.delete_collection()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="documentation",
        persist_directory="./chroma_db"
    )

    return vector_store, len(chunks)


# -----------------------------------------
# 5. Process the document
# -----------------------------------------

def process_document(file_name=None, file_bytes=None):

    documents = load_document(
        file_name=file_name,
        file_bytes=file_bytes
    )

    vector_store, chunk_count = create_vector_store(documents)

    return vector_store, chunk_count


# -----------------------------------------
# 6. Answer questions with source citations
# -----------------------------------------

def answer_question(vector_store, question):

    retrieved_docs = vector_store.similarity_search(
        question,
        k=3
    )

    if not retrieved_docs:
        return (
            "I could not find the answer in the uploaded document.",
            []
        )

    context_parts = []
    sources = []
    source_groups = {}

    # Give each retrieved chunk a citation label.
    for index, document in enumerate(retrieved_docs, start=1):

        label = f"Source {index}"

        context_parts.append(
            f"[{label}]\n{document.page_content}"
        )

        source_name = document.metadata.get(
            "source",
            "Unknown document"
        )

        page_number = document.metadata.get("page")

        # Group chunks that come from the same file and page.
        source_key = (source_name, page_number)

        if source_key not in source_groups:

            source_groups[source_key] = {
                "source": source_name,
                "page": page_number,
                "labels": []
            }

            sources.append(source_groups[source_key])

        source_groups[source_key]["labels"].append(label)

    context = "\n\n".join(context_parts)

    prompt = f"""
You are a helpful technical documentation assistant.

Answer the user's question using ONLY the provided context.

CITATION RULES:
1. Add citations such as [Source 1] to claims supported by the context.
2. Use only the source labels actually provided below.
3. Do not invent citations or page numbers.
4. If the answer is not present in the context, say:
   "I could not find the answer in the uploaded document."
5. Explain the answer clearly and simply.

Context:
{context}

Question:
{question}

Answer:
"""

    response = get_llm().invoke(prompt)

    return response.content, sources
