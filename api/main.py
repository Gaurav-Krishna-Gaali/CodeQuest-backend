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


# Helper function to call the Piston API
def execute_code_on_piston(
    modified_code: str,
    input_value: str,
    language: str = "python",
    version: str = "3.10.0",
) -> dict:
    payload = {
        "language": language,
        "version": version,
        "files": [{"name": "solution.py", "content": modified_code}],
        "stdin": input_value,
        "args": [],
        "compile_timeout": 10000,
        "run_timeout": 3000,
        "run_memory_limit": -1,
    }

    try:
        response = requests.post(PISTON_URL, json=payload)
        print(response.content)
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error with Piston API request: {e}")
        raise HTTPException(
            status_code=500, detail="Error executing code on Piston API"
        )

    return response.json()


@app.post("/submit-solution")
async def submit_solution(solution: SolutionRequest):
    try:
        test_cases = fetch_test_cases_for_question(solution.question_id)
        modified_code = solution.code
        test_results = []

        for test_case in test_cases:
            input_value = test_case["input"]
            expected_output = test_case["expected_output"]

            result = execute_code_on_piston(
                modified_code, input_value, solution.language, solution.version
            )
            print(result)

            actual_output = (
                result.get("run", "").get("output", "").strip()
            )  # Safely get the output
            pass_test = actual_output == expected_output

            test_results.append(
                {
                    "id": test_case["id"],
                    "input": input_value,
                    "expected_output": expected_output,
                    "actual_output": actual_output,
                    "pass": pass_test,
                }
            )

        # Return the results of all test cases
        return JSONResponse(test_results)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
