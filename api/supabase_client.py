from supabase import create_client, Client
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# Your Supabase URL and API Key
url = os.environ["FAST_API_SUPABASE_URL"]
key = os.environ["FAST_API_SUPABASE_API_KEY"]
supabase: Client = create_client(url, key)


def fetch_users():
    users = supabase.table("users").select("*").execute()
    return users.data


def get_user_id_by_provider(provider_id: str):
    try:
        response = (
            supabase.table("users")
            .select("id")
            .eq("provider_id", provider_id)
            .execute()
        )
        return response.data[0]["id"]
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


def insert_solution(solution):
    print(solution)
    try:
        solution_data = {
            "user_id": get_user_id_by_provider(solution["provider_id"]),
            "question_id": solution["question_id"],
            "submitted_code": solution["code"],
            "is_correct": solution["is_correct"],
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        }

        existing_solution = (
            supabase.table("solutions")
            .select("*")
            .eq("user_id", solution_data["user_id"])
            .eq("question_id", solution_data["question_id"])
            .execute()
        )
        if existing_solution.data:
            response = (
                supabase.table("solutions")
                .update(solution_data)
                .eq("user_id", solution_data["user_id"])
                .eq("question_id", solution_data["question_id"])
                .execute()
            )
            print("Updated existing solution:", response)
        else:
            response = supabase.table("solutions").insert(solution_data).execute()
            print("Inserted new solution:", response)
        return response.data
    except Exception as e:
        print(f"Error inserting solution: {e}")


def insert_user(user_data):
    try:
        response = supabase.table("users").insert(user_data).execute()
        return response.data
    except Exception as e:
        print(f"Error inserting user: {e}")
        return None


def fetch_questions():
    questions = supabase.table("questions").select("*").execute()
    return questions.data


def fetch_solutions_for_user(user_id):
    solutions = supabase.table("solutions").select("*").eq("user_id", user_id).execute()
    return solutions.data


def fetch_test_cases_for_question(question_id):
    test_cases = (
        supabase.table("test_cases")
        .select("*")
        .eq("question_id", question_id)
        .execute()
    )
    return test_cases.data


if __name__ == "__main__":
    users = fetch_users()
    print("Users:", users)

    questions = fetch_questions()
    print("Questions:", questions)

    # Fetch solutions for a specific user (e.g., user_id = 1)
    solutions = fetch_solutions_for_user(1)
    print("Solutions for user 1:", solutions)

    # Fetch test cases for a specific question (e.g., question_id = 1)
    test_cases = fetch_test_cases_for_question(1)
    print("Test cases for question 1:", test_cases)

    provider_id = "7e5ff3c2-c57a-496c-bee4-1ac277c87f14"
    user_id = get_user_id_by_provider(provider_id)
    print("User ID:", user_id)
