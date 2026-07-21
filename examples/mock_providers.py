"""
Runnable example with mock providers — no network, no credentials.

Shows the two cases that matter: models that agree, and models that don't.
Run:  python examples/mock_providers.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from consensus_lens import Lens, Provider


# Three "models" that mostly agree ------------------------------------------
def agree_a(prompt): return "The migration is low risk if backups are verified first."
def agree_b(prompt): return "Migration risk is low provided backups are verified beforehand."
def agree_c(prompt): return "Low risk migration, as long as verified backups exist first."

# One provider that simply fails --------------------------------------------
def flaky(prompt): raise RuntimeError("429 rate limited")


def demo(title, providers):
    print(f"\n=== {title} ===")
    lens = Lens(providers)
    r = lens.ask("Assess the risk of this migration plan.")
    print(f"consensus={r.consensus}  level={r.level}  counted={r.counted}/{r.total}")
    for v in r.votes:
        tag = "counted" if v.counted else f"skipped ({v.status})"
        print(f"  {v.name:10} {v.latency_ms:>4}ms  {tag}")


if __name__ == "__main__":
    demo("models agree", [
        Provider("model-a", agree_a),
        Provider("model-b", agree_b),
        Provider("model-c", agree_c),
    ])

    demo("one provider fails, vote continues honestly", [
        Provider("model-a", agree_a),
        Provider("model-b", agree_b),
        Provider("flaky",   flaky),
    ])
