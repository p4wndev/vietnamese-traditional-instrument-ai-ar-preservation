import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.schemas import RAGRequest, RAGOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/rag", response_model=RAGOut)
async def rag_query(body: RAGRequest):
    """
    Answer a question about Vietnamese traditional instruments using
    Retrieval-Augmented Generation (FAISS + OpenAI).
    """
    from app.core.lifespan import state

    chain = state.get("rag_chain")
    if chain is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG chatbot is not available (check OPENAI_API_KEY and FAISS_DB_PATH)",
        )

    try:
        response = chain.invoke({"query": body.question})
    except Exception as exc:
        logger.exception("RAG chain error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG error: {exc}",
        )

    answer: str = response.get("result", "")
    source_docs = response.get("source_documents", [])
    sources = [doc.page_content for doc in source_docs]

    return RAGOut(answer=answer, sources=sources)
