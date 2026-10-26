# flipbench

Measure how much of a small local model's yes/no verdict is about the code and how
much is about the prompt.

## Why

I use a local model as a first-pass auditor: one yes/no question per code snippet
("does this backtest use future information?"). That setup has an obvious failure mode
nobody measures: the verdict depends on how you phrase the question.

This repo measures it. Same snippets, same question, three prompt layouts, two runs
per cell, two small quantised models, with the trivial baselines reported next to the
accuracy.

## Result on 6 snippets / 72 calls

| model | accuracy | always-YES baseline | YES rate | abstentions |
|---|---|---|---|---|
| gemma-2-2b-it Q4_K_M | 19/36 = 52.8% | 18/36 = 50.0% | 75.0% | 0 |
| qwen2.5-coder-1.5b Q4_K_M | 18/36 = 50.0% | 18/36 = 50.0% | 100.0% | 0 |

- qwen answered YES on 36/36 calls: stable, and therefore uninformative.
- gemma changed its verdict on 4 of 6 snippets when only the layout changed. On two
  of them the flip was deterministic: YES with the code first, NO with the question
  first, twice each.
- The UNSURE instruction moved nothing: 0 abstentions in 72 calls.

Full write-up: POST_DRAFT.md. Raw rows: runs/*.jsonl. Numbers: runs/summary.txt.

## Run

Needs a llama.cpp build with llama-cli, plus two GGUF models. Point the harness at
them with environment variables:

    export FLIPBENCH_LLAMA_CLI=/path/to/llama-cli
    export FLIPBENCH_LLAMA_LIB=/path/to/lib
    export FLIPBENCH_GEMMA=/path/to/gemma.gguf
    export FLIPBENCH_QWEN=/path/to/qwen.gguf

    python3 -m flipbench.runner --model gemma --runs 2 --out runs/gemma.jsonl
    python3 -m flipbench.runner --model qwen  --runs 2 --out runs/qwen.jsonl
    python3 -m flipbench.analyze runs/gemma.jsonl runs/qwen.jsonl

About 8s per call for gemma, 6s for qwen, ~4 minutes per model on a CPU-only box.

## Files

- flipbench/dataset.jsonl - 6 snippets, 3 with a real defect, 3 pattern false positives
- flipbench/variants.py - the three prompt layouts
- flipbench/runner.py - runs llama-cli, stores full stdout, parses the verdict
- flipbench/analyze.py - run-to-run flips, abstention, accuracy, trivial baselines,
  per-layout accuracy, and per-item layout sensitivity
- runs/summary.txt - analyzer output for the committed runs
- runs/*.buggy1026 - rows produced by a parser bug, kept for the record, excluded
  from every number above

## Parser note

llama-cli in this build echoes the prompt even with --no-display-prompt, and the
prompt itself contains the words YES / NO / UNSURE. Parsing the first such token in
stdout reads the prompt, not the model. The first version of this harness did exactly
that and reported YES for all 36 gemma calls, 9 of which were actually NO.

The parser now cuts at the last `Answer:` marker and reads from there. Full stdout is
stored per row, so any row can be re-checked without re-running the model.

## Limits

- 6 items. A smoke test, not a benchmark.
- Ground truth is my own reading of each snippet, not external adjudication.
- Two small 4-bit models; nothing here generalises to larger models.
- No seed control, so run-to-run flips include sampling noise.
- One machine, CPU only, temperature 0.2, 16-token answers.

## License

MIT, see LICENSE.
