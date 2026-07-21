<p align="center"><img src="cover.svg" alt="consensus-lens" width="100%"></p>

# llm-consensus-lens

**Fan out one prompt across many language models. See where they agree, where they don't, and how far apart they really are.**

Created by **Yacine Mahboub**, Founder of WEVIA.

---

## The idea

A single model gives you one answer with false confidence. Several models give you a *distribution* — and the shape of that distribution is information.

`llm-consensus-lens` sends the same prompt to every provider you configure, in parallel, then measures how much the answers actually overlap. High agreement is a signal you can trust the result. Low agreement is a signal to look closer — and it's exactly the case a single model would have hidden from you.

This is the evaluation skeleton, not a product. It ships with **no providers wired in** and **no business logic**. You bring the models; it brings the discipline.

## What it does

- **Fan-out**: one prompt → N providers, concurrently, with per-provider timeouts.
- **Graceful degradation**: a provider that rate-limits, errors, or times out is recorded as such and excluded from the vote — never faked, never silently dropped.
- **Consensus scoring**: pairwise token-overlap (Jaccard) across the answers, aggregated into a single agreement score.
- **Honest reporting**: every answer is tagged with its latency, status, and whether it counted toward consensus.

## What it deliberately does *not* do

- It does not pick a "winner". Consensus is a measurement, not a verdict.
- It does not retry silently or paper over failures. A 429 is reported as a 429.
- It does not ship provider credentials, endpoints, or routing logic. That is yours.

## Quick look

```python
from consensus_lens import Lens, Provider

lens = Lens(providers=[
    Provider("model-a", call=call_model_a),
    Provider("model-b", call=call_model_b),
    Provider("model-c", call=call_model_c),
])

result = lens.ask("Summarize the risks of this migration plan.")

print(result.consensus)        # 0.0 - 1.0
print(result.level)            # "strong" | "partial" | "divergent"
for v in result.votes:
    print(v.name, v.status, v.latency_ms)
```

## Why the consensus number matters

A high score means the models converged independently — the kind of corroboration you cannot get from one model no matter how large. A low score is not a failure of the tool; it is the tool doing its job, telling you the question is genuinely contested and deserves a human.

The most dangerous answer in production is a confident one that happens to be wrong. This measures the confidence you can actually justify.

## Design principles

The scoring engine follows a small set of operational doctrines — the same ones we apply to agents that touch production. See [github.com/Yacineutt/agent-ops-doctrines](https://github.com/Yacineutt/agent-ops-doctrines). The relevant one here is *honesty over fluency*: an absent answer is absent, never invented to keep the vote tidy.

## License

Apache-2.0 — see [LICENSE](LICENSE).

---

*Maintained by [WEVIA](https://weval-consulting.com) — sovereign AI platform engineering.*
