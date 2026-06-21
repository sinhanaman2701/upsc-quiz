import pytest
from services.parser.rule_based import detect_groups, parse_questions

CHAPTER_TEXT = """POLITY - Revise through Theme Wise MCQs 400+ MCQs (PART-1)
CHAPTER – 1 BASIC CONCEPTS OF POLITY AND CONSTITUTION
1. The right to a fair trial is an example of which kind of rights?
(a) Civil rights
(b) Political rights
(c) Social rights
(d) Economic rights
1. Answer: A
Explanation:
Civil rights encompass individual liberties related to legal proceedings.

2. Which of the following are characteristics of Socialism?
1. Flexible economic system
2. Government control
(a) 1 and 2 only
(b) 3 and 4 only
(c) 2 and 3 only
(d) 1, 2, 3 and 4
2. Answer: A
Explanation:
Socialism is a political and economic theory.

CHAPTER – 2 HISTORICAL BACKGROUND
3. Which act introduced provincial autonomy?
(a) Act of 1909
(b) Act of 1919
(c) Act of 1935
(d) Act of 1947
3. Answer: C
Explanation:
The Government of India Act 1935 introduced provincial autonomy.
"""

SECTION_TEXT = """
SECTION A – ANCIENT HISTORY
1. When did Harappa civilization flourish?
(a) 2500 BC
(b) 1500 BC
(c) 3000 BC
(d) 1000 BC
1. Answer: A
Explanation: Harappa flourished around 2500 BC.
"""

NO_GROUP_TEXT = """
1. What is the capital of India?
(a) Mumbai
(b) New Delhi
(c) Kolkata
(d) Chennai
1. Answer: B
Explanation: New Delhi is the capital.

2. How many states in India?
(a) 25
(b) 26
(c) 28
(d) 29
2. Answer: C
Explanation: India has 28 states.
"""

def test_detect_chapter_groups():
    pages = [(1, CHAPTER_TEXT)]
    groups = detect_groups(pages)
    assert len(groups) == 2
    assert groups[0]["group_type"] == "chapter"
    assert "BASIC CONCEPTS" in groups[0]["display_name"]
    assert groups[1]["group_type"] == "chapter"
    assert "HISTORICAL BACKGROUND" in groups[1]["display_name"]

def test_detect_section_groups():
    pages = [(1, SECTION_TEXT)]
    groups = detect_groups(pages)
    assert len(groups) == 1
    assert groups[0]["group_type"] == "section"

def test_detect_no_groups_returns_all_questions():
    pages = [(1, NO_GROUP_TEXT)]
    groups = detect_groups(pages)
    assert len(groups) == 1
    assert groups[0]["group_type"] == "none"
    assert groups[0]["display_name"] == "All Questions"

def test_parse_questions_extracts_all_fields():
    questions = parse_questions(CHAPTER_TEXT)
    assert len(questions) >= 1
    q = questions[0]
    assert q["question_text"] != ""
    assert q["options"]["a"] != ""
    assert q["options"]["b"] != ""
    assert q["correct_answer"] in ("a", "b", "c", "d")
    assert q["confidence"] == 1.0

def test_parse_questions_order_index():
    questions = parse_questions(CHAPTER_TEXT)
    indices = [q["order_index"] for q in questions]
    assert indices == list(range(1, len(questions) + 1))

def test_parse_question_missing_answer_gives_low_confidence():
    text = """1. What is photosynthesis?
(a) Process A
(b) Process B
(c) Process C
(d) Process D
"""
    questions = parse_questions(text)
    assert len(questions) == 1
    assert questions[0]["confidence"] < 1.0
    assert questions[0]["correct_answer"] is None
