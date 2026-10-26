"""Run one local model over the dataset and prompt variants."""
import argparse, json, os, re, subprocess, sys, time

from .variants import VARIANTS

LLAMA_CLI = os.environ.get(
    "FLIPBENCH_LLAMA_CLI", "/root/slothaudit/bin/llama/llama-b11804/llama-cli")
LLAMA_LIB = os.environ.get("FLIPBENCH_LLAMA_LIB", os.path.dirname(LLAMA_CLI))
MODELS = {
    "qwen": os.environ.get(
        "FLIPBENCH_QWEN", "/root/slothaudit/models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"),
    "gemma": os.environ.get(
        "FLIPBENCH_GEMMA", "/root/slothaudit/models/gemma-2-2b-it-Q4_K_M.gguf"),
}


def ask(prompt, gguf, timeout=180):
    env = dict(os.environ, LD_LIBRARY_PATH=LLAMA_LIB)
    cmd = [LLAMA_CLI, "-m", gguf, "-p", prompt, "-n", "16", "--temp", "0.2",
           "--no-display-prompt", "-st", "--no-show-timings"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, stdin=subprocess.DEVNULL)
    return p.stdout.strip()


def parse(text):
    """Verdict = first word after the LAST "Answer:" marker.

    llama-cli in this build still echoes the prompt, and the prompt
    contains YES / NO / UNSURE, so parsing the first token of the whole
    output reads the prompt instead of the model. Anchor on the last
    "Answer:" marker, then take the first verdict word after it.
    """
    up = text.upper()
    idx = up.rfind("ANSWER:")
    tail = up[idx + 7:] if idx != -1 else up
    words = tail.replace(".", " ").replace(",", " ").replace(":", " ").split()
    for w in words:
        if w in ("YES", "NO", "UNSURE"):
            return w
    return "UNPARSED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    gguf = MODELS[a.model]
    rows = [json.loads(l) for l in open("flipbench/dataset.jsonl", encoding="utf-8") if l.strip()]
    if a.limit:
        rows = rows[: a.limit]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for item in rows:
            for vname, fn in VARIANTS.items():
                prompt = fn(item["code"], item["question"])
                for r in range(a.runs):
                    t0 = time.time()
                    raw = ask(prompt, gguf)
                    rec = {"item": item["id"], "variant": vname, "run": r,
                           "verdict": parse(raw), "raw": raw, "secs": round(time.time() - t0, 1)}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    print(rec["item"], vname, r, rec["verdict"], rec["secs"], flush=True)


if __name__ == "__main__":
    main()
