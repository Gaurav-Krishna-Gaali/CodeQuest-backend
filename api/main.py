from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from .supabase_client import fetch_questions, fetch_test_cases_for_question
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/questions")
async def get_questions():
    try:
        questions = fetch_questions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(questions)


@app.get("/questions/{question_id}")
async def get_question(question_id: int):
    try:
        questions = fetch_questions()
        question = next((q for q in questions if q["id"] == question_id), None)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(question)


@app.get("/questions/{question_id}/test_cases")
async def get_test_cases(question_id: int):
    try:
        test_cases = fetch_test_cases_for_question(question_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(test_cases)
