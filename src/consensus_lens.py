"""
llm-consensus-lens — fan out one prompt across many models, measure agreement.

Created by Yacine Mahboub, Founder of WEVIA.
Licensed under Apache-2.0.

This is a provider-agnostic skeleton. It contains NO credentials, NO endpoints,
and NO business logic. You supply the callables that reach your models.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, Optional
import re
import time
import itertools


# ---- data model -------------------------------------------------------------

@dataclass
class Provider:
    """A single model endpoint.

    `call` receives the prompt string and must return the model's text answer.
    It may raise; failures are captured, never propagated into the vote.
    """
    name: str
    call: Callable[[str], str]
    timeout_s: float = 30.0


@dataclass
class Vote:
    name: str
    status: str            # "ok" | "error" | "timeout"
    text: Optional[str]
    latency_ms: int
    counted: bool          # did this vote enter the consensus computation?
    error: Optional[str] = None


@dataclass
class Result:
    votes: list[Vote]
    consensus: float       # 0.0 - 1.0, average pairwise Jaccard of "ok" votes
    level: str             # "strong" | "partial" | "divergent" | "insufficient"
    counted: int
    total: int
    meta: dict = field(default_factory=dict)


# ---- tokenization & scoring -------------------------------------------------

_WORD = re.compile(r"[a-z0-9]+")

def _tokens(text: str) -> set[str]:
    """Lowercase word-set. Deliberately simple and language-agnostic.

    Swap this for embeddings or a semantic scorer if you need meaning-level
    agreement rather than surface overlap — the interface stays the same.
    """
    return set(_WORD.findall(text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _classify(score: float, counted: int) -> str:
    if counted < 2:
        return "insufficient"      # cannot measure agreement with < 2 answers
    if score >= 0.60:
        return "strong"
    if score >= 0.30:
        return "partial"
    return "divergent"


# ---- the lens ---------------------------------------------------------------

class Lens:
    """Fan a prompt out across providers and score their agreement."""

    def __init__(self, providers: list[Provider], strong_at: float = 0.60,
                 partial_at: float = 0.30):
        if not providers:
            raise ValueError("Lens requires at least one provider.")
        self.providers = providers
        self.strong_at = strong_at
        self.partial_at = partial_at

    def _invoke(self, p: Provider, prompt: str) -> Vote:
        start = time.monotonic()
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(p.call, prompt)
            try:
                text = fut.result(timeout=p.timeout_s)
                ms = int((time.monotonic() - start) * 1000)
                # An empty answer is a non-answer: recorded, not counted.
                if not text or not text.strip():
                    return Vote(p.name, "error", None, ms, False,
                                error="empty response")
                return Vote(p.name, "ok", text, ms, True)
            except FuturesTimeout:
                ms = int((time.monotonic() - start) * 1000)
                return Vote(p.name, "timeout", None, ms, False,
                            error=f"exceeded {p.timeout_s}s")
            except Exception as e:  # noqa: BLE001 — capture is the point
                ms = int((time.monotonic() - start) * 1000)
                return Vote(p.name, "error", None, ms, False, error=str(e))

    def ask(self, prompt: str) -> Result:
        # Fan out concurrently. One slow provider must not block the rest.
        with ThreadPoolExecutor(max_workers=len(self.providers)) as ex:
            votes = list(ex.map(lambda p: self._invoke(p, prompt),
                                self.providers))

        ok = [v for v in votes if v.counted and v.text]
        counted = len(ok)

        if counted < 2:
            return Result(votes, 0.0, _classify(0.0, counted),
                          counted, len(votes),
                          meta={"note": "need >= 2 answers to score agreement"})

        toks = {v.name: _tokens(v.text) for v in ok}
        pairs = list(itertools.combinations(ok, 2))
        score = sum(_jaccard(toks[a.name], toks[b.name])
                    for a, b in pairs) / len(pairs)

        return Result(
            votes=votes,
            consensus=round(score, 4),
            level=_classify(score, counted),
            counted=counted,
            total=len(votes),
            meta={"pairs": len(pairs)},
        )
