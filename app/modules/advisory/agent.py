import os
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.modules.advisory import models
from . import schemas, prompts

# Initialize Gemini
# Uses settings for API Key
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", 
    temperature=0.7,
    google_api_key=settings.GOOGLE_API_KEY
)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def retrieve_context(query: str, company_id: str, k: int = 3) -> List[models.AdvisoryKnowledgeBase]:
    """Retrieve relevant documents using vector similarity."""
    db: Session = SessionLocal() # specialized session for vector op
    try:
        # Generate embedding for query
        query_embedding = embeddings.embed_query(query)
        
        # PGVector similarity search
        # Note: syntax depends on valid pgvector setup in SQLAlchemy model
        # Assuming model has `embedding` column defined with correct Type
        
        results = db.query(models.AdvisoryKnowledgeBase).filter(
            models.AdvisoryKnowledgeBase.company_id == company_id
        ).order_by(
            models.AdvisoryKnowledgeBase.embedding.l2_distance(query_embedding)
        ).limit(k).all()
        
        return results
    except Exception as e:
        print(f"Error in RAG retrieval: {e}")
        return []
    finally:
        db.close()

async def run_agent(request: schemas.ChatRequest, user_context: dict = None) -> schemas.AdvisoryResponse:
    company_id = request.company_id
    if not company_id and user_context:
        company_id = user_context.get("company_id")
        
    # 1. Retrieve Context
    context_docs = []
    if company_id:
        context_docs = retrieve_context(request.user_message, str(company_id))
    
    context_text = "\n\n".join([f"Source: {doc.source_title}\nContent: {doc.content}" for doc in context_docs])
    
    # 2. Construct Prompt
    # Combining persona with retrieved context
    system_prompt = f"""{prompts.CFO_PERSONA}
    
    Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context:
    {context_text}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])
    
    # 3. Chain
    chain = prompt | llm | StrOutputParser()
    
    # 4. Invoke
    try:
        response_text = await chain.ainvoke({"question": request.user_message})
    except Exception as e:
        response_text = f"I'm sorry, I encountered an error processing your request: {e}"

    sources = [doc.source_title for doc in context_docs]

    return schemas.AdvisoryResponse(
        response=response_text,
        session_id=request.session_id or "new_session",
        sources=sources
    )
