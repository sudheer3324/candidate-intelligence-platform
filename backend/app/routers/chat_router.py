from fastapi import APIRouter
from app import schemas
from app.rag.chat import answer_question

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest):
    try:
        answer, sources = answer_question(payload.question, top_k=payload.top_k)
    except Exception as e:
        return schemas.ChatResponse(
            answer=(
                "I couldn't reach Gemini to answer that. Double-check that GEMINI_API_KEY is set "
                f"correctly in backend/.env and that you have internet access.\n\nDetails: {e}"
            ),
            sources=[],
        )
    return schemas.ChatResponse(answer=answer, sources=sources)
