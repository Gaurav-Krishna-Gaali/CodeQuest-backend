from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from .supabase_client import (
    fetch_questions,
    fetch_test_cases_for_question,
    insert_user,
    insert_solution,
    fetch_solutions_for_user,
    get_user_id_by_provider,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://code-quest-rosy.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PISTON_URL = "https://emkc.org/api/v2/piston/execute"


class SolutionRequest(BaseModel):
    question_id: int
    provider_id: str
    code: str
    language: str = "python"
    version: str = "3.10.0"


class UserRequest(BaseModel):
    email: str
    username: str = None
    profile_pic: str = None
    provider: str
    provider_id: str


class SubmittedSolution(BaseModel):
    question_id: str
    submitted_code: str = None
    is_correct: bool = False
    submitted_at: str


@app.post("/login")
async def login_user(user: UserRequest):
    try:
        result = insert_user(user.dict())
        if not result:
            raise HTTPException(status_code=500, detail="Failed to insert user")
        return {"message": "User logged in successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


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
    input_value: list,
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
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error with Piston API request: {e}")
        raise HTTPException(
            status_code=500, detail="Error executing code on Piston API"
        )

    return response.json()


def replace_main_block(testcase, code):
    pattern = r'if __name__ == "__main__":\s*print\(main\(input\(\)\)\)'
    return re.sub(pattern, f"print(main({testcase}))", code)


@app.post("/submit-solution")
async def submit_solution(solution: SolutionRequest):
    try:
        test_cases = fetch_test_cases_for_question(solution.question_id)
        modified_code = solution.code

        test_results = []
        all_tests_passed = True

        for test_case in test_cases:
            input_value = test_case["input"]
            expected_output = test_case["expected_output"]
            new_modified_code = replace_main_block(test_case["input"], modified_code)

            result = execute_code_on_piston(
                new_modified_code, input_value, solution.language, solution.version
            )

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

            if not pass_test:
                print(f"Test {test_case['id']} failed")
                all_tests_passed = False

        if all_tests_passed:
            print("All tests passed")
            solution_dict = solution.dict()
            solution_dict["is_correct"] = True
            insert_solution(solution_dict)
        else:
            print("Not all tests passed")
            solution_dict = solution.dict()
            solution_dict["is_correct"] = False
            print(solution_dict)
            insert_solution(solution_dict)

        return JSONResponse(test_results)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/solutions/{provider_id}")
async def get_solutions(provider_id: str):
    try:
        user_id = get_user_id_by_provider(provider_id)
        solutions = fetch_solutions_for_user(user_id)
        solutions_collection = [
            {k: v for k, v in solution.items() if k != "user_id"}
            for solution in solutions
        ]
        return JSONResponse(solutions_collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
