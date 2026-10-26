# Same code, same question, three layouts: the verdict moved, the code did not

I built a small harness to answer one narrow question: when a local model answers
"is there a lookahead bug in this snippet?", how much of that answer is about the code?

Short answer: on a 2B model, not much. Move the question above the code and the
verdict flips - deterministically, on both runs.

## Setup

- 6 snippets from real backtest-review work: 3 with a genuine defect (lookahead,
  omitted fees, grid-search maximum reported as strategy performance), 3 that
  match a suspicious pattern but are correct.
- 3 prompt layouts, identical content otherwise:
  - E = evidence first: code, then question
  - Q = question first: question, then code
  - H = evidence first plus "if the code does not contain enough information,
    answer UNSURE. Do not guess."
- 2 runs per cell, temperature 0.2, 16-token cap, CPU only, llama.cpp b11804.
- Two models: gemma-2-2b-it Q4_K_M and qwen2.5-coder-1.5b-instruct Q4_K_M.
- 72 calls total.

Ground truth is my own reading of each snippet, recorded before the runs.

## Result 1: the 1.5B model answers YES to everything

qwen2.5-coder-1.5b returned YES on 36 of 36 calls, under all three layouts.

Exactly half the items are positive, so an always-YES model scores 50%. It scored
50.0%. Zero abstentions, zero flips: perfectly stable and perfectly uninformative.
Stability and usefulness are different properties, and a fixed-answer model gets a
perfect score on the stability one.

## Result 2: the 2B model lands inside the trivial baseline

| model | accuracy | always-YES baseline | YES rate | abstentions |
|---|---|---|---|---|
| gemma-2-2b-it | 19/36 = 52.8% | 18/36 = 50.0% | 75.0% | 0 |
| qwen2.5-coder-1.5b | 18/36 = 50.0% | 18/36 = 50.0% | 100.0% | 0 |

One correct answer above the always-YES baseline, on 36 calls. That is not a
capability, it is rounding.

The UNSURE instruction changed nothing: 0 abstentions across 72 calls. Both models
answered with full confidence every single time.

## Result 3: 4 of 6 items change verdict when only the layout changes

Per item, in order E | Q | H, one character per run:

| item | truth | E | Q | H | |
|---|---|---|---|---|---|
| lookahead | defect | YY | NN | YY | layout-sensitive |
| fee_missing | defect | YY | NN | YY | layout-sensitive |
| grid_select | defect | YY | YY | YY | stable |
| fee_named_other | clean | NY | NN | YY | layout-sensitive |
| rolling_ok | clean | YY | YY | NN | layout-sensitive |
| label_shift | clean | YY | YY | YY | stable |

Two of these are not noise. lookahead and fee_missing were answered YES twice with
the code first, and NO twice with the question first. Same model, same text, same
temperature - only the order changed, and the flip reproduced.

Adding the UNSURE hint moved rolling_ok from YES, YES to NO, NO.

Only one cell in the whole grid is plain run-to-run noise: fee_named_other under E,
which gave NO then YES.

## What I take from it

If a verdict changes when you move the question above the code, that verdict is not
a measurement of the code. It is a measurement of the prompt.

Concretely: one ask per finding is not enough for anything automated. Either ask the
same item under several layouts and report the disagreement as a confidence signal,
or keep the model as a pointer and let a human read the snippet.

Also: consistency is not evidence. The most consistent model here never looked at
the code.

## A bug I found in my own harness

The first version of this bench printed YES for all 36 gemma calls. Not because the
model agreed with itself, but because the parser never read the model.

This llama.cpp build still echoes the prompt next to the answer
(--no-display-prompt notwithstanding). The prompt contains the sentence "Answer with
exactly one word: YES, NO, or UNSURE", and my parser took the first YES/NO/UNSURE
token in stdout - which is that sentence, not the model output.

After the fix, 9 of 36 cells changed, every one of them from YES to NO: each was a NO
the model had actually produced and the parser had overwritten. Rows from the buggy
parser are kept in runs/*.buggy1026 and are counted nowhere above.

Fix: keep full stdout, cut at the last Answer: marker, parse from there. Everything
above comes from the fixed parser, and the harness now stores complete output so any
row can be re-checked.

The lesson is not "check your parser". It is that a harness with this bug reports a
perfectly stable, perfectly wrong model, and nothing in the output looks broken.

## Limits

- 6 items. A smoke test, not a benchmark.
- Ground truth is my own reading, not outside adjudication.
- Two small 4-bit models. Nothing here says anything about 7B+ models.
- No seed control, so run-to-run flips include sampling noise.
- One machine, CPU only.

## Reproduce

    python3 -m flipbench.runner --model gemma --runs 2 --out runs/gemma.jsonl
    python3 -m flipbench.runner --model qwen  --runs 2 --out runs/qwen.jsonl
    python3 -m flipbench.analyze runs/gemma.jsonl runs/qwen.jsonl

Roughly 8s per call for gemma, 6s for qwen, about 4 minutes per model here.

Code: repo not published yet.
