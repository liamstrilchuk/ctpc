import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from pygments import lex
from pygments.lexers import get_lexer_by_name
from models import db, Problem, ScaleFactor

def tokenize_code(code, lang_alias):
    """Tokenize code using Pygments for syntax-based comparison."""
    try:
        lexer = get_lexer_by_name(lang_alias)
        tokens = [token for _, token in lex(code, lexer)]
        return ' '.join(tokens)
    except Exception:
        return code

def compare_to_ai_solutions(user_code, problem_id, lang):
    """
    Compare user code to AI solutions for the given problem using
    tokenized TF-IDF vectors + cosine similarity.
    Returns a scaled similarity score between 0–100.
    """
    problem = db.session.query(Problem).filter_by(id=problem_id).first()
    scale_factor = db.session.query(ScaleFactor).filter_by(problem_id=problem_id, language_id=lang.grader_id).first()

    if not problem:
        print("Problem not found in DB.")
        return 0

    ai_entries = [s for s in problem.ai_solutions]
    if not ai_entries:
        print("No AI solutions for this problem.")
        return 0

    tokenized_user = tokenize_code(user_code, lang.short_name)
    tokenized_ai_list = [tokenize_code(entry.code, lang.short_name) for entry in ai_entries if entry.language_id==lang.grader_id]

    scores = []
    for tokenized_ai in tokenized_ai_list:
        all_docs = tokenized_ai_list + [tokenized_user, tokenized_ai]
        vectorizer = TfidfVectorizer(tokenizer=str.split, lowercase=False)
        tfidf_matrix = vectorizer.fit_transform(all_docs)

        user_vector = tfidf_matrix[-2]
        ai_vector = tfidf_matrix[-1]

        sim = cosine_similarity(user_vector, ai_vector).flatten()[0]
        scores.append(sim)

    if not scores:
        print("No AI solutions of the correct language")
        return 0

    best_score = max(scores)
    avg_score = sum(scores) / len(scores)
    raw_score = (best_score * 0.5 + avg_score * 0.5)

    scaled_score = raw_score * scale_factor.value
    final_score = min(scaled_score * 100, 100)

    return round(final_score, 2)
