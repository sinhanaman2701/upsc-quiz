import re

# Group detection patterns — order matters: try chapter first, then section/part/topic
GROUP_PATTERNS = [
    ("chapter", re.compile(
        r'CHAPTER\s*[–\-]\s*\d+\s+([A-Z][^\n]+)', re.IGNORECASE
    )),
    ("section", re.compile(
        r'SECTION\s+[A-Z\d]+\s*[–\-]?\s*([A-Z][^\n]+)', re.IGNORECASE
    )),
    ("part", re.compile(
        r'PART\s+[A-Z\d]+\s*[–\-]?\s*([A-Z][^\n]*)', re.IGNORECASE
    )),
    ("topic", re.compile(
        r'TOPIC\s*[–\-]?\s*\d*\s*[:\-]?\s*([A-Z][^\n]+)', re.IGNORECASE
    )),
]

# Matches answer line: "N. Answer: X" and optional explanation block
ANSWER_BLOCK_PATTERN = re.compile(
    r'(?m)^(\d+)\.\s+[Aa]nswer\s*[:\.]?\s*([A-Da-d])[ \t]*\n'
    r'(?:[Ee]xplanation\s*[:\.]?[ \t]*\n?(.*?))?(?=\n\d+\.|\Z)',
    re.DOTALL
)

# Matches a single option line: (a) text ... up to next option, next numbered item, or end
OPTION_PATTERN = re.compile(
    r'\(([abcdABCD])\)\s*(.+?)(?=\n\s*\([abcdABCD]\)|\n\d+\.|\Z)',
    re.DOTALL
)

# Matches a question that has NO answer line (question with ? followed by options but no answer)
Q_WITH_OPTIONS_ONLY = re.compile(
    r'(?m)^(\d+)\.\s+(.*?\?[^\n]*\n(?:.+\n)*?)\(a\)',
    re.DOTALL
)


def detect_groups(pages: list[tuple[int, str]]) -> list[dict]:
    full_text = "\n".join(text for _, text in pages)

    for group_type, pattern in GROUP_PATTERNS:
        matches = list(pattern.finditer(full_text))
        if matches:
            groups = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                # Keep original case from the match (don't .title() it)
                display_name = f"{group_type.capitalize()} {i+1}: {match.group(1).strip()}"
                groups.append({
                    "display_name": display_name,
                    "group_type": group_type,
                    "start_page": _find_page_for_offset(pages, start),
                    "raw_text": full_text[start:end],
                    "order_index": i,
                })
            return groups

    # No grouping found — return single group
    return [{
        "display_name": "All Questions",
        "group_type": "none",
        "start_page": 1,
        "raw_text": full_text,
        "order_index": 0,
    }]


def parse_questions(raw_text: str) -> list[dict]:
    questions = []

    # Find all answer blocks and track their positions
    answer_matches = list(ANSWER_BLOCK_PATTERN.finditer(raw_text))

    if answer_matches:
        # Parse questions that have answers: search window = text between prev answer end and current answer start
        prev_end = 0
        for ans_m in answer_matches:
            q_num = ans_m.group(1)
            correct_answer = ans_m.group(2).lower()
            explanation_raw = ans_m.group(3)
            explanation = explanation_raw.strip() if explanation_raw else None

            # Search window: from previous answer block end to start of current answer marker
            window = raw_text[prev_end:ans_m.start()]

            # Find the question start: "q_num. <text with ?>"
            q_start_pat = re.compile(
                r'(?m)^' + re.escape(q_num) + r'\.\s+(.*?\?[^\n]*)',
                re.DOTALL
            )
            qm = q_start_pat.search(window)

            if qm:
                q_block = window[qm.start():]
                # Question text: from start up to first option
                first_opt = OPTION_PATTERN.search(q_block)
                if first_opt:
                    question_text = q_block[:first_opt.start()].strip()
                    # Remove the leading "N. " prefix from question text
                    question_text = re.sub(r'^\d+\.\s+', '', question_text)
                else:
                    question_text = re.sub(r'^\d+\.\s+', '', q_block.strip())

                # Extract options
                options = {"a": "", "b": "", "c": "", "d": ""}
                for opt_m in OPTION_PATTERN.finditer(q_block):
                    key = opt_m.group(1).lower()
                    val = opt_m.group(2).strip()
                    if key in options:
                        options[key] = val
            else:
                question_text = ""
                options = {"a": "", "b": "", "c": "", "d": ""}

            all_fields = (
                question_text and
                all(options[k] for k in ("a", "b", "c", "d")) and
                correct_answer is not None
            )
            confidence = 1.0 if all_fields else 0.0

            questions.append({
                "order_index": len(questions) + 1,
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "confidence": confidence,
            })

            prev_end = ans_m.end()

    else:
        # No answer markers found — look for questions with options only
        # Find all question blocks by looking for "N. text?" followed by options
        # Use a pattern that captures full block up to next question or end
        q_blocks = _find_questions_without_answers(raw_text)
        for i, (q_num, q_block) in enumerate(q_blocks):
            first_opt = OPTION_PATTERN.search(q_block)
            if first_opt:
                question_text = q_block[:first_opt.start()].strip()
                question_text = re.sub(r'^\d+\.\s+', '', question_text)
            else:
                question_text = re.sub(r'^\d+\.\s+', '', q_block.strip())

            options = {"a": "", "b": "", "c": "", "d": ""}
            for opt_m in OPTION_PATTERN.finditer(q_block):
                key = opt_m.group(1).lower()
                val = opt_m.group(2).strip()
                if key in options:
                    options[key] = val

            all_fields = (
                question_text and
                all(options[k] for k in ("a", "b", "c", "d"))
            )
            confidence = 0.0  # No answer available

            questions.append({
                "order_index": i + 1,
                "question_text": question_text,
                "options": options,
                "correct_answer": None,
                "explanation": None,
                "confidence": confidence,
            })

    return questions


def _find_questions_without_answers(raw_text: str) -> list[tuple[str, str]]:
    """Find question blocks that have options but no answer marker."""
    # Find question starts that contain a '?'
    q_start_pattern = re.compile(r'(?m)^(\d+)\.\s+(?!Answer).*\?', re.IGNORECASE)
    starts = list(q_start_pattern.finditer(raw_text))

    results = []
    for i, sm in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(raw_text)
        q_block = raw_text[sm.start():end]
        results.append((sm.group(1), q_block))

    return results


def _find_page_for_offset(pages: list[tuple[int, str]], offset: int) -> int:
    cumulative = 0
    for page_num, text in pages:
        cumulative += len(text) + 1
        if offset < cumulative:
            return page_num
    return pages[-1][0] if pages else 1
