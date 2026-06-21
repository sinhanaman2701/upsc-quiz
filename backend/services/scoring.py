def calculate_score(responses: list[dict], questions_by_id: dict) -> tuple[int, list[dict]]:
    """
    responses: [{question_id, selected}]
    questions_by_id: {str(id): question_doc}
    Returns (score, breakdown)
    """
    score = 0
    breakdown = []
    for resp in responses:
        q = questions_by_id.get(resp["question_id"])
        if not q:
            continue
        is_correct = resp["selected"].lower() == q["correct_answer"].lower()
        if is_correct:
            score += 1
        breakdown.append({
            "question_id": resp["question_id"],
            "question_text": q["question_text"],
            "options": q["options"],
            "selected": resp["selected"],
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
            "explanation": q.get("explanation"),
        })
    return score, breakdown
