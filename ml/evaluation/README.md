# Evaluation harness

MVP roadmap item 2 (docs/product/mvp-scope.md): "Evaluation framework + benchmark dataset."
Two complementary pieces, one dataset:

- **`run_eval.py`** — a live, human-readable report. Hits a running `optimization-service`
  over HTTP and prints per-prompt and aggregate metrics (token reduction, confidence,
  latency, estimated cost saved). Zero third-party dependencies (stdlib only) so it's
  runnable against any running instance, local or deployed, without a venv.
- **`../../services/optimization-service/tests/evaluation/test_benchmark_regression.py`** —
  the CI-friendly counterpart. Runs the *same* dataset in-process (no server, no network,
  LLM step disabled) and asserts aggregate bounds, so a change that quietly makes
  optimization worse or the safety/validation checks looser fails the test suite instead
  of only showing up as a smaller number in a report nobody reads.
- **`datasets/benchmark_prompts.jsonl`** — the shared dataset both read. Each line:
  `{"id", "category", "mode", "expect_reduction", "text"}`. Categories cover coding, SQL,
  documentation, research, business, long-context, and multi-turn-style prompts, plus a
  few "already minimal" baseline prompts (`expect_reduction: false`) to catch
  false-positive compression.

## Run it

```bash
# 1. start the backend (see services/optimization-service/README.md)
cd services/optimization-service && ./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# 2. in another terminal, from the repo root:
python ml/evaluation/run_eval.py
```

Results are also written to `results/<timestamp>.json` (gitignored — regenerated per run).

## Scope — what this does and doesn't measure

Measured: token reduction %, semantic-preservation scores from the deterministic
validator (confidence / semanticSimilarity / constraintPreservation, ADR-006), latency,
estimated cost saved.

**Deliberately not measured**: "task success" (would the optimized prompt still get a
correct answer from a downstream model) and "hallucination risk". Both need an LLM-as-judge
or a human rater, which the project has already decided against as a default — see ADR-006
(LLM-as-judge rejected as the default validator) and ADR-011/012's standing rule against
metrics with no real signal behind them. If that tradeoff is ever worth making, it belongs
here as an additional, clearly-labeled optional pass — not folded silently into these numbers.

## A note on what building this actually found

Writing the dataset surfaced two real, honest gaps rather than just filling in a checklist:

1. Two prompts originally tested *only* whitespace cleanup — but whitespace isn't counted
   as a token by the heuristic tokenizer (`packages/tokenizers`), so a whitespace-only
   cleanup can shrink the text without moving the token count at all. Fixed by adding a
   genuine duplicate phrase to those prompts, since that was the real original intent.
2. A `conservative`-mode prompt used a duplicate *sentence* inline, but conservative mode
   only dedupes at line granularity (see `DeterministicCompressionStrategy`'s docstring) —
   sentence-level dedup only kicks in at `balanced` and above. Fixed by making the
   duplicate a full duplicate line, matching what conservative mode actually does.

Both are documented here rather than quietly patched, since they're a useful reminder that
"reduction %" depends on the tokenizer's definition of a token, and that mode tiers are a
real behavioral difference, not just a label.
