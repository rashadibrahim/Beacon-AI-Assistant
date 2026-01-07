"""RAG (Retrieval-Augmented Generation) tools for document processing."""
from pathlib import Path
from typing import List
from langchain_core.tools import create_retriever_tool
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    UnstructuredExcelLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_classic.schema import Document


SUPPORTED_EXTENSIONS = {
    '.txt': TextLoader,
    '.pdf': PyPDFLoader,
    '.csv': CSVLoader,
    '.xlsx': UnstructuredExcelLoader,
    '.xls': UnstructuredExcelLoader,
}


def prepare_rag_vector_store(documents_path: str) -> bool:
    """
    Prepare RAG vector store for documents in the specified path.
    
    Scans the documents path for supported file types (.txt, .pdf, .csv, .xlsx, .xls),
    loads them, and creates a FAISS vector store using SentenceTransformer embeddings.
    If no documents are found, returns False.
    
    Args:
        documents_path: Path to the directory containing documents
        
    Returns:
        True if documents were found and vector store was created successfully, False otherwise
    """
    documents_path = Path(documents_path)
    
    # Check if path exists
    if not documents_path.exists():
        print(f"Documents path does not exist: {documents_path}")
        return False
    
    # Load documents
    documents = []
    for file_path in documents_path.rglob("*"):
        if file_path.is_file():
            extension = file_path.suffix.lower()
            
            if extension in SUPPORTED_EXTENSIONS:
                try:
                    loader_class = SUPPORTED_EXTENSIONS[extension]
                    loader = loader_class(str(file_path))
                    loaded_docs = loader.load()
                    documents.extend(loaded_docs)
                    print(f"Loaded {len(loaded_docs)} documents from {file_path.name}")
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
    
    if not documents:
        print("No documents found")
        return False
    
    try:
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks")
        
        # Create embeddings using SentenceTransformer
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create vector store
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save vector store
        vector_store_path = documents_path / ".vector_store"
        vector_store_path.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(vector_store_path))
        print(f"Vector store saved to {vector_store_path}")
        
        return True
        
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return False


def get_retriever_tool(documents_path: str, k: int = 2, description: str = None):
    """
    Load an existing vector store and return a retriever tool.

    Args:
        documents_path: Path to the directory containing documents and .vector_store
        k: Number of documents to retrieve
        description: Custom description for the tool (what documents it contains)

    Returns:
        LangChain tool for document retrieval, or None if vector store not available
    """
    documents_path = Path(documents_path)
    vector_store_path = documents_path / ".vector_store"

    if not vector_store_path.exists():
        print(f"Vector store not found at {vector_store_path}")
        return None

    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = FAISS.load_local(
            str(vector_store_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        
        # Use custom description if provided, otherwise use a generic one
        tool_description = description if description else (
            "Retrieves relevant documents from the knowledge base. "
            "Use this tool when the user asks questions that might be answered by documents in the system."
        )
        
        retriever_tool = create_retriever_tool(
            retriever=retriever,
            name="document_retriever",
            description=tool_description,
        )
        return retriever_tool
    except Exception as e:
        print(f"Error loading vector store: {e}")
        return None

