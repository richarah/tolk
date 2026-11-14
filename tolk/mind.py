"""The loop that ties parsing, choosing, storing, the engine and answering together."""

from dataclasses import dataclass

from tolk import compile as comp, engine, erg, lf, say, sem, store
from tolk.ask import Answer, answer


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
        k, x = comp.choose(readings, store.known_preds(self.db))
        printed = lf.show(x)
        if isinstance(x, lf.Refusal):
            return Result(k + 1, len(readings), printed, printed)
        if isinstance(x, lf.Ask):
            a = answer(self.db, x)
            return Result(k + 1, len(readings), printed, self._answer_text(a), a)
        sid = store.add_sentence(self.db, text)
        if isinstance(x, lf.Tell):
            added = store.tell(self.db, x, sid)
            engine.run(self.db)
            outcome = f"stored, {len(added)} new fact(s)"
        else:
            store.add_rule(self.db, x, sid)
            engine.run(self.db)
            outcome = "rule stored"
        return Result(k + 1, len(readings), printed, outcome)

    def tell(self, text: str) -> Result:
        return self.hear(text)

    def ask(self, text: str) -> Result:
        return self.hear(text)

    def _answer_text(self, a: Answer) -> str:
        proofs = "\n".join(say.proof_text(self.db, p) for solution in a.proofs for p in solution)
        head = say.answer_text(self.db, a)
        return f"{head}\n{proofs}" if proofs else head
