#!/usr/bin/env python3
"""
AWS Practice Exam Grader
Usage: python grade_exam.py practice-exam/practice-exam-1.md
"""
import re
import sys
import os


def parse_answers(raw):
    """Parse answer text in both formats: 'A, B' (exams 1-12) and 'AB' (exams 13-23)."""
    raw = raw.strip().rstrip(',').strip()
    # Comma/space separated: "A, B" or "A B"
    if re.search(r'[,\s]', raw):
        parts = frozenset(a.strip() for a in re.split(r'[,\s]+', raw) if re.match(r'^[A-E]$', a.strip()))
        if parts:
            return parts
    # Concatenated: "AB" or "ACD"
    parts = frozenset(c for c in raw.upper() if c in 'ABCDE')
    return parts


def parse_exam(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Remove YAML frontmatter
    content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)

    questions = []
    sequential = 0  # fallback counter for non-sequential numbering (e.g. all "1.")

    # Split content into question blocks by matching numbered items
    blocks = re.split(r'\n(?=\d+\. )', content)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Match question number and text
        header_match = re.match(r'^(\d+)\.\s+(.+?)(?=\n\s*-\s+[A-E]\.)', block, re.DOTALL)
        if not header_match:
            continue

        sequential += 1
        stated_num = int(header_match.group(1))
        # If all questions have the same number (e.g. all "1."), use sequential counter
        num = sequential if stated_num == 1 and sequential > 1 else stated_num
        question_text = ' '.join(header_match.group(2).split())  # normalize whitespace

        # Extract answer from <details> block — handle both "Correct answer:" and "Correct Answer:"
        answer_match = re.search(
            r'<details[^>]*>.*?Correct\s+[Aa]nswer:\s*([A-E][A-E,\s]*?)[\s\n]*(?:Explanation|</details>)',
            block, re.DOTALL
        )
        if not answer_match:
            continue

        correct_answers = parse_answers(answer_match.group(1))
        if not correct_answers:
            continue

        # Extract options (lines like "- A. ...")
        options = re.findall(r'-\s+([A-E]\..+?)(?=\n\s*-\s+[A-E]\.|\n\s*<details|\Z)', block, re.DOTALL)
        options = [' '.join(o.split()) for o in options]

        questions.append({
            'num': num,
            'text': question_text,
            'options': options,
            'answers': correct_answers,
            'multi': len(correct_answers) > 1,
        })

    # If stated numbers are non-sequential (all 1.), keep insertion order
    nums = [q['num'] for q in questions]
    if len(set(nums)) < len(nums):
        # Duplicates — renumber by order
        for i, q in enumerate(questions, 1):
            q['num'] = i
        return questions

    return sorted(questions, key=lambda q: q['num'])


def run_exam(questions):
    exam_name = "AWS Cloud Practitioner Practice Exam"
    print("\n" + "=" * 62)
    print(f"  {exam_name}")
    print(f"  {len(questions)} questions  |  Pass threshold: 70%")
    print("=" * 62)
    print("  Single answer : type the letter  (e.g.  B)")
    print("  Multi-answer  : separate by space or comma  (e.g.  A, C)")
    print("  Press Ctrl+C to quit at any time.")
    print("=" * 62 + "\n")

    user_answers = []

    for i, q in enumerate(questions, 1):
        print(f"Question {q['num']} of {len(questions)}")
        print(f"{q['text']}")
        for opt in q['options']:
            print(f"  {opt}")
        if q['multi']:
            print(f"  (Choose {len(q['answers'])})")

        while True:
            raw = input("\n  Your answer: ").strip().upper()
            if not raw:
                continue
            parsed = frozenset(a.strip() for a in re.split(r'[,\s]+', raw) if re.match(r'^[A-E]$', a.strip()))
            if parsed:
                break
            print("  Invalid input — enter letters A through E only.")

        user_answers.append(parsed)
        print()

    return user_answers


def grade(questions, user_answers):
    correct_count = 0
    wrong = []

    for q, ua in zip(questions, user_answers):
        if ua == q['answers']:
            correct_count += 1
        else:
            wrong.append((q, ua))

    total = len(questions)
    pct = correct_count / total * 100
    passed = pct >= 70

    print("\n" + "=" * 62)
    print("  RESULTS")
    print("=" * 62)
    print(f"  Score  : {correct_count}/{total}  ({pct:.1f}%)")
    print(f"  Result : {'PASS' if passed else 'FAIL'}")
    print("=" * 62)

    if wrong:
        print(f"\n  You got {len(wrong)} question(s) wrong:\n")
        for q, ua in wrong:
            print(f"  Q{q['num']}: {q['text']}")
            for opt in q['options']:
                letter = opt[0]
                if letter in q['answers'] and letter in ua:
                    tag = "  <- correct (your answer)"
                elif letter in q['answers']:
                    tag = "  <- correct answer"
                elif letter in ua:
                    tag = "  <- your answer (wrong)"
                else:
                    tag = ""
                print(f"    {opt}{tag}")
            print(f"    Your answer   : {', '.join(sorted(ua))}")
            print(f"    Correct answer: {', '.join(sorted(q['answers']))}")
            print()

    print("=" * 62 + "\n")


def main():
    if len(sys.argv) < 2:
        script = os.path.basename(sys.argv[0])
        print(f"Usage: python {script} <exam-file.md>")
        print(f"Example: python {script} practice-exam/practice-exam-1.md")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)

    questions = parse_exam(filepath)
    if not questions:
        print("Error: no questions found in the exam file.")
        sys.exit(1)

    print(f"Loaded {len(questions)} questions from '{os.path.basename(filepath)}'.")

    try:
        user_answers = run_exam(questions)
        grade(questions, user_answers)
    except KeyboardInterrupt:
        print("\n\nExam aborted.\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
