from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from .supabase_client import fetch_questions, fetch_test_cases_for_question
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PISTON_URL = "https://emkc.org/api/v2/piston/execute"


class SolutionRequest(BaseModel):
    question_id: int
    code: str
    language: str = "python"
    version: str = "3.10.0"


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/questions")
async def get_questions():
    try:
        questions = fetch_questions()
        return JSONResponse(questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{question_id}")
async def get_question(question_id: int):
    try:
        questions = fetch_questions()
        question = next((q for q in questions if q["id"] == question_id), None)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return JSONResponse(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{question_id}/test_cases")
async def get_test_cases(question_id: int):
    try:
        test_cases = fetch_test_cases_for_question(question_id)
        return JSONResponse(test_cases)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-solution")
async def submit_solution(request: SolutionRequest):
    try:
        test_cases = fetch_test_cases_for_question(request.question_id)
        if not test_cases:
            raise HTTPException(
                status_code=404, detail="No test cases found for this question"
            )

        results = []
        total_pass = 0

        for test_case in test_cases:
            input_data = test_case["input"]
            expected_output = test_case["expected_output"]

            payload = {
                "language": request.language,
                "version": request.version,
                "files": [{"name": "solution.py", "content": request.code}],
                "stdin": input_data,
            }

            try:
                response = requests.post(PISTON_URL, json=payload)
                response.raise_for_status()
            except requests.RequestException as e:
                results.append(
                    {
                        "input": input_data,
                        "error": f"Failed to run code: {str(e)}",
                    }
                )
                continue

            output = response.json()
            stdout = output.get("run", {}).get("stdout", "").strip()
            stderr = output.get("run", {}).get("stderr", "")
            status_code = output.get("run", {}).get("code", 1)

            if status_code != 0:
                results.append(
                    {
                        "input": input_data,
                        "expected_output": expected_output,
                        "output": None,
                        "error": stderr.strip() or "Runtime error",
                        "status": "Fail",
                    }
                )
            else:
                is_pass = stdout == expected_output
                if is_pass:
                    total_pass += 1

                results.append(
                    {
                        "input": input_data,
                        "expected_output": expected_output,
                        "output": stdout,
                        "status": "Pass" if is_pass else "Fail",
                    }
                )

        return {
            "question_id": request.question_id,
            "total_test_cases": len(test_cases),
            "passed": total_pass,
            "failed": len(test_cases) - total_pass,
            "results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
