import os
import openai
from dotenv import load_dotenv
from models import db, AISolution, ScaleFactor, LanguageType

from .similarity import compare_to_ai_solutions
from utils.languages import language_types

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_ai_solution(problem_description, language):
    """
    Generate a single AI solution using the OpenAI Chat API.
    Returns the generated code as a string.
    """
    prompt_template = (
        f"Write a concise {language} function to solve the following problem. "
        f"Do not include explanations, only the code:\n\n{problem_description}\n\n"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_template}],
            max_tokens=5000,
            temperature=0.6
        )

        if not response.choices:
            print("No choices returned.")

        code = response.choices[0].message.content.strip()
        if not code:
            print("Empty code response.")

        return code

    except Exception as e:
        print(f"Failed: {e}")

    return None

def initialize_solutions(problem, problem_description, sol_count, scale_count, scale_target):
    db.session.query(AISolution).filter_by(problem_id=problem.id).delete()
    db.session.commit()

    for lang in db.session.query(LanguageType):
        for i in range(sol_count):
            code = generate_ai_solution(problem_description, lang.name)

            ai_solution = AISolution(problem_id=problem.id, language_id=lang.grader_id, code=code)
            db.session.add(ai_solution)

        unscaled = []

        scale_factor = ScaleFactor(value=1, problem_id=problem.id, language_id=lang.grader_id)
        db.session.add(scale_factor)
        db.session.commit()

        for i in range(scale_count):
            code = generate_ai_solution(problem_description, lang.name)

            score = compare_to_ai_solutions(code, problem.id, lang)
            unscaled.append(score)

        scale_val = scale_target / (sum(unscaled) / scale_count)
        scale_factor.value = scale_val
        db.session.commit()

    db.session.merge(problem)
    db.session.commit()