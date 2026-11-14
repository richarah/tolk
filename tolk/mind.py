"""The loop that ties parsing, choosing, storing, the engine and answering together."""

from dataclasses import dataclass

from tolk import compile as comp, engine, erg, lf, say, sem, store
from tolk.ask import Answer, answer, prove


@dataclass(frozen=True)
class Result:
    reading: int  # 1-based reading that was chosen
    of: int  # how many readings the parser returned
    printed: str
    outcome: str
    answer: Answer | None = None


class Mind:
    def __init__(self, path: str = ":memory:") -> None:
        self.db = store.open_store(path)

    def hear(self, text: str) -> Result:
        readings = [sem.read(raw) for raw in erg.parse(text)]
        k, x = comp.choose(readings, store.known_preds(self.db), self._lookup)
        printed = lf.show(x)
        head = (k + 1, len(readings), printed)
        if isinstance(x, lf.Refusal):
            return Result(*head, outcome="refused")
        if isinstance(x, lf.Ask):
            a = answer(self.db, x)
            return Result(*head, outcome=self._answer_text(a), answer=a)
        if isinstance(x, lf.Same):
            sid = store.add_sentence(self.db, text)
            store.merge(self.db, x.a, x.b, sid)
            engine.run(self.db)
            return Result(*head, outcome=f"one thing: {x.a.id} and {x.b.id}")
        if isinstance(x, lf.Rule):
            refusal = engine.check(self.db, x)
            if refusal is not None:
                return Result(*head, outcome=lf.show(refusal))
            sid = store.add_sentence(self.db, text)
            store.add_rule(self.db, x, sid)
            engine.run(self.db)
            return Result(*head, outcome="rule stored")
        sid = store.add_sentence(self.db, text)
        stored = store.tell(self.db, x, sid)
        if isinstance(stored, lf.Refusal):
            opposite = prove(self.db, int(stored.detail))
            return Result(*head, outcome=f"refused, contradicts:\n{say.proof_text(self.db, opposite)}")
        engine.run(self.db)
        return Result(*head, outcome=f"stored, {len(stored)} new fact(s)")

    def tell(self, text: str) -> Result:
        return self.hear(text)

    def ask(self, text: str) -> Result:
        return self.hear(text)

    def _lookup(self, pred: str) -> set[str]:
        return store.things_with(self.db, pred)

    def _answer_text(self, a: Answer) -> str:
        proofs = "\n".join(say.proof_text(self.db, p) for solution in a.proofs for p in solution)
        head = say.answer_text(self.db, a)
        return f"{head}\n{proofs}" if proofs else head
