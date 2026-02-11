import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredEPubLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from app.core.config import settings

# Setup database connection string for pgvector
# langchain-postgres requires a specific format, often the same as sqlalchemy
CONNECTION_STRING = settings.DB_URL

def get_loader(file_path: str):
    if file_path.endswith(".pdf"):
        return PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        return TextLoader(file_path)
    elif file_path.endswith(".epub"):
        return UnstructuredEPubLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def ingest_books(directory: str):
    print(f"Scanning directory: {directory}")
    files = glob.glob(os.path.join(directory, "**/*.*"), recursive=True)
    
    documents = []
    for file_path in files:
        if file_path.endswith((".pdf", ".txt", ".epub")):
            print(f"Loading {file_path}...")
            try:
                loader = get_loader(file_path)
                docs = loader.load()
                # Add metadata
                for doc in docs:
                    doc.metadata["source_title"] = os.path.basename(file_path)
                    doc.metadata["source_type"] = "book"
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    if not documents:
        print("No documents found.")
        return

    print(f"Loaded {len(documents)} documents. Splitting...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    print(f"Created {len(splits)} chunks. Embedding and storing...")
    
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    
    store = PGVector(
        embeddings=embeddings,
        collection_name="advisory_knowledge_base",
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )
    
    store.add_documents(splits)
    print("Ingestion complete.")

if __name__ == "__main__":
    # Create data directory if not exists
    os.makedirs("./data/books", exist_ok=True)
    ingest_books("./data/books")
