"""Three prompt variants for the same yes/no question."""

def evidence_first(code, question):
    return (
        "You are auditing a trading backtest. Answer with exactly one word: YES, NO, or UNSURE.\n\n"
        "CODE:\n" + code.strip() + "\n\nQUESTION: " + question.strip() + "\n\nAnswer:"
    )

def question_first(code, question):
    return (
        "Answer with exactly one word: YES, NO, or UNSURE.\n\n"
        "QUESTION: " + question.strip() + "\n\nCODE:\n" + code.strip() + "\n\nAnswer:"
    )

def with_hint(code, question):
    return (
        "You are auditing a trading backtest. Answer with exactly one word: YES, NO, or UNSURE.\n"
        "If the code does not contain enough information, answer UNSURE. Do not guess.\n\n"
        "CODE:\n" + code.strip() + "\n\nQUESTION: " + question.strip() + "\n\nAnswer:"
    )

VARIANTS = {
    "evidence_first": evidence_first,
    "question_first": question_first,
    "with_hint": with_hint,
}
