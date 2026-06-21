import re

# Group detection patterns — order matters: try chapter first, then section/part/topic
GROUP_PATTERNS = [
    # group 1 = identifier (number/letter), group 2 = title text
    ("chapter", re.compile(
        r'CHAPTER\s*[–\-]\s*(\d+)\s+([A-Z][^\n]+)', re.IGNORECASE
    )),
    ("section", re.compile(
        r'SECTION\s+([A-Z\d]+)\s*[–\-]?\s*([A-Z][^\n]+)', re.IGNORECASE
    )),
    ("part", re.compile(
        r'PART\s+([A-Z\d]+)\s*[–\-]?\s*([A-Z][^\n]*)', re.IGNORECASE
    )),
    ("topic", re.compile(
        r'TOPIC\s*[–\-]?\s*(\d*)\s*[:\-]?\s*([A-Z][^\n]+)', re.IGNORECASE
    )),
]

# Answer block — handles:  "N. Answer: C"  "N. Answer: (C)"  "N. Ans: C"  "N. Ans. (C)"
ANSWER_BLOCK_PATTERN = re.compile(
    r'(?m)^(\d+)\.\s+Ans(?:wer)?\s*[:\.]?\s*\(?([A-Da-d])\)?[ \t]*\n'
    r'(?:Explanation\s*[:\.]?[ \t]*\n?(.*?))?(?=\n\d+\.|\Z)',
    re.DOTALL | re.IGNORECASE
)

# Lookahead that matches a line beginning with any option indicator: (a), a., a)
_NEXT_OPT_LA = r'\n[ \t]*(?:\([abcdABCD]\)|[abcdABCD][.)])'

# Option line pattern — handles: (a) text, a. text, a) text (and uppercase variants)
#   group 1 = letter in paren-style "(a)", group 2 = letter in dot/paren-style "a.", group 3 = text
OPTION_PATTERN = re.compile(
    r'(?:^|\n)[ \t]*(?:\(([abcdABCD])\)|([abcdABCD])[.)])[ \t]+'
    r'(.+?)'
    r'(?=' + _NEXT_OPT_LA + r'|\n\d+\.|\Z)',
    re.DOTALL
)


def _opt_key(m) -> str:
    """Return the option letter from an OPTION_PATTERN match (handles both style groups)."""
    return (m.group(1) or m.group(2)).lower()


def _opt_text(m) -> str:
    return m.group(3).strip()


def detect_groups(pages: list[tuple[int, str]]) -> list[dict]:
    full_text = "\n".join(text for _, text in pages)

    for group_type, pattern in GROUP_PATTERNS:
        matches = list(pattern.finditer(full_text))
        if matches:
            groups = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                identifier = match.group(1).strip()
                raw_title = match.group(2).strip()
                # Remove ToC artifacts: trailing dots and page numbers (e.g. "......... 3")
                clean_title = re.sub(r'[\s.]{3,}\d+\s*$', '', raw_title).strip()
                clean_title = re.sub(r'\s+\d+\s*$', '', clean_title).strip()
                display_name = f"{group_type.capitalize()} {identifier}: {clean_title.title()}"
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
    answer_matches = list(ANSWER_BLOCK_PATTERN.finditer(raw_text))

    if answer_matches:
        prev_end = 0
        for ans_m in answer_matches:
            q_num = ans_m.group(1)
            correct_answer = ans_m.group(2).lower()
            explanation_raw = ans_m.group(3)
            explanation = explanation_raw.strip() if explanation_raw else None

            # Search window: text between previous answer block end and this answer marker
            window = raw_text[prev_end:ans_m.start()]

            # Question start: "q_num. <text>" ending at first option line or at "q_num. Ans"
            q_start_pat = re.compile(
                r'(?m)^' + re.escape(q_num) + r'\.\s+(.*?)(?='
                + _NEXT_OPT_LA + r'|\n' + re.escape(q_num) + r'\.\s+Ans)',
                re.DOTALL | re.IGNORECASE
            )
            qm = q_start_pat.search(window)

            if qm:
                q_block = window[qm.start():]
                first_opt = OPTION_PATTERN.search(q_block)
                if first_opt:
                    question_text = q_block[:first_opt.start()].strip()
                else:
                    question_text = q_block.strip()
                question_text = re.sub(r'^\d+\.\s+', '', question_text)

                options = {"a": "", "b": "", "c": "", "d": ""}
                for opt_m in OPTION_PATTERN.finditer(q_block):
                    key = _opt_key(opt_m)
                    if key in options:
                        options[key] = _opt_text(opt_m)

                # raw_text stored for LLM validator: full question block + answer line
                raw_q_text = (window[qm.start():] + ans_m.group(0)).strip()
            else:
                question_text = ""
                options = {"a": "", "b": "", "c": "", "d": ""}
                raw_q_text = ans_m.group(0).strip()

            all_fields = (
                question_text and
                all(options[k] for k in ("a", "b", "c", "d")) and
                correct_answer is not None
            )

            questions.append({
                "order_index": len(questions) + 1,
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "confidence": 1.0 if all_fields else 0.0,
                "raw_text": raw_q_text,
            })

            prev_end = ans_m.end()

    else:
        # No answer markers — look for questions with options only
        for i, (q_num, q_block) in enumerate(_find_questions_without_answers(raw_text)):
            first_opt = OPTION_PATTERN.search(q_block)
            if first_opt:
                question_text = q_block[:first_opt.start()].strip()
                question_text = re.sub(r'^\d+\.\s+', '', question_text)
            else:
                question_text = re.sub(r'^\d+\.\s+', '', q_block.strip())

            options = {"a": "", "b": "", "c": "", "d": ""}
            for opt_m in OPTION_PATTERN.finditer(q_block):
                key = _opt_key(opt_m)
                if key in options:
                    options[key] = _opt_text(opt_m)

            questions.append({
                "order_index": i + 1,
                "question_text": question_text,
                "options": options,
                "correct_answer": None,
                "explanation": None,
                "confidence": 0.0,
                "raw_text": q_block.strip(),
            })

    return questions


def _find_questions_without_answers(raw_text: str) -> list[tuple[str, str]]:
    """Find question blocks that have options (any format) but no answer marker."""
    q_start_pattern = re.compile(
        r'(?m)^(\d+)\.\s+(?!Ans)(?=.*(?:\([abcdABCD]\)|[abcdABCD][.)]))',
        re.IGNORECASE
    )
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
