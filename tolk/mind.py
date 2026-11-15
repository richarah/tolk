"""The loop that ties parsing, choosing, storing, the engine and answering together."""

import dataclasses
import re
from dataclasses import dataclass

from tolk import compile as comp, comparison, defaults, engine, diagnosis, history, lf, negation, ordering, proposals, report, say, sem, store, words
from tolk.diagnosis import Diagnosis
from tolk.rules import claims
from tolk.rules.comparatives import PREFIX
from tolk.proposals import Proposal
from tolk.ask import Answer, answer, prove
from tolk.lf import Atom, Var


# A sentence told as an observation has this trust, the highest, and is never a candidate for removal.
OBSERVED = 1_000_000
FORGET = re.compile(r"forget that (.+?)\.?", re.IGNORECASE)


@dataclass(frozen=True)
class Result:
    reading: int  # 1-based reading that was chosen
    of: int  # how many readings the parser returned
    printed: str
    outcome: str
    answer: Answer | None = None


class Mind:
    def __init__(self, path: str = ":memory:", policy: tuple[str, ...] = ("specific",), auto_revise: bool = False) -> None:
        self.db = store.open_store(path)
        self.set_policy(policy)
        self.db.execute("INSERT INTO meta(key, value) VALUES ('auto_revise', ?)", (str(int(auto_revise)),))
        self.ctx = "world"  # the current context: "world", or a supposition's name
        self._suppositions = 0
        self._ran: list[tuple[int, int | None]] = []

    @property
    def policy(self) -> tuple[str, ...]:
        (value,) = self.db.execute("SELECT value FROM meta WHERE key = 'policy'").fetchone()
        return tuple(p for p in value.split(",") if p)

    def set_policy(self, policy: tuple[str, ...]) -> None:
        """The conflict policy is stored with the facts it was used to derive. Changing it rebuilds them."""
        unknown = [p for p in policy if p not in defaults.POLICIES]
        if unknown:
            raise ValueError(f"unknown policy criteria {unknown}; choose from {defaults.POLICIES}")
        with self.db:
            self.db.execute("INSERT INTO meta(key, value) VALUES ('policy', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (",".join(policy),))
            if defaults.has_defaults(self.db):
                defaults.rebuild(self.db, getattr(self, "ctx", "world"), policy)

    @property
    def auto_revise(self) -> bool:
        return self.db.execute("SELECT value FROM meta WHERE key = 'auto_revise'").fetchone()[0] == "1"

    def hear(self, text: str, trust: int = 0, observation: bool = False) -> Result:
        with self.db:  # an error part way through rolls the whole sentence back, so a bug cannot store half a rule
            before = self._conflicts()
            result = self._hear(text, trust, observation)
            fresh = self._conflicts() - before
            if not fresh:
                return result
            if not self.auto_revise:
                return dataclasses.replace(result, outcome=result.outcome + "\n" + diagnosis.report(self.db, fresh))
            said = []
            while fresh:
                candidates = next((d.candidates for d in self.diagnose() if d.conflict in fresh), ())
                if not candidates:
                    said.append("conflict with nothing to retract: " + "; ".join(f"{a} against {b}" for a, b in sorted(fresh)))
                    break
                said.append(f'retracted "{candidates[0].text}" to end a conflict')
                self._retract(candidates[0].sentence, "auto-revised")
                fresh = self._conflicts() - before
            return dataclasses.replace(result, outcome="\n".join([result.outcome] + said))

    def observe(self, text: str) -> Result:
        """A tell at the highest trust. An observation may contradict what is derived, and is never removed to end a conflict."""
        return self.hear(text, OBSERVED, observation=True)

    def retract(self, sentence_id: int, reason: str = "retracted") -> None:
        """Remove what a sentence told, and rebuild what was derived from it. The sentence row stays, with the reason in revision."""
        with self.db:
            self._retract(sentence_id, reason)

    def _retract(self, sentence_id: int, reason: str) -> None:
        if self.db.execute("SELECT 1 FROM merge WHERE sentence = ?", (sentence_id,)).fetchone():
            raise ValueError("an identity cannot be retracted: the facts it merged were rewritten onto one thing")
        history.retract(self.db, sentence_id, reason)
        defaults.rebuild(self.db, self.ctx, self.policy)

    def _conflicts(self) -> set[tuple[str, str]]:
        return {(say.fact_text(self.db, p), say.fact_text(self.db, n)) for p, n in self.db.execute("SELECT positive_fact, negative_fact FROM conflict")}

    def diagnose(self) -> list[Diagnosis]:
        return diagnosis.diagnose(self.db)

    def _forget(self, target: str) -> Result:
        readings, k, x = self._read(target)
        head = (k + 1, len(readings), lf.show(x))
        if isinstance(x, (lf.Refusal, lf.Ask, lf.Describe, lf.Every, lf.Extreme)):
            return Result(*head, outcome="refused: only a statement can be forgotten")
        found = history.latest_told(self.db, lf.show(x), self.ctx)
        if found is None:
            return Result(*head, outcome="nothing that was told means that")
        if self.db.execute("SELECT 1 FROM merge WHERE sentence = ?", (found[0],)).fetchone():
            return Result(*head, outcome="refused: an identity cannot be forgotten")
        self._retract(found[0], f'forget that {target}')
        return Result(*head, outcome=f'forgot "{found[1]}"')

    def _read(self, text: str) -> tuple[list, int, lf.LF]:
        """Parse, and choose a reading. A sentence refused for a word the grammar does not know gets one more try with every class offered."""
        readings = [sem.read(p.mrs, p.lex) for p in words.parse(self.db, text)]
        k, x = comp.choose(readings, store.known_preds(self.db), self._lookup, self._history)
        if isinstance(x, lf.Refusal) and x.code == "UNKNOWN_WORD":
            again = [sem.read(p.mrs, p.lex) for p in words.offered(text, readings)]
            k2, x2 = comp.choose(again, store.known_preds(self.db), self._lookup, self._history) if again else (k, x)
            if not isinstance(x2, lf.Refusal):
                return again, k2, x2
        return readings, k, x

    def _derive(self) -> None:
        defaults.refresh(self.db, self.ctx, self.policy)

    def _hear(self, text: str, trust: int = 0, observation: bool = False) -> Result:
        forgetting = FORGET.fullmatch(text.strip())
        if forgetting:
            return self._forget(forgetting.group(1) + ".")
        readings, k, x = self._read(text)
        printed = lf.show(x)
        head = (k + 1, len(readings), printed)
        if isinstance(x, lf.Refusal):
            return Result(*head, outcome="refused")
        if isinstance(x, lf.Ask):
            x = report.bind_claims(self.db, x) if x.claims else x
            a = x if isinstance(x, Answer) else answer(self.db, x, self.ctx)
            return Result(*head, outcome=report.answer_text(self.db, a), answer=a)
        if isinstance(x, lf.Every):
            value, by_default = defaults.universal(self.db, x, self.policy)
            a = Answer(value, (), (), by_default=by_default)
            return Result(*head, outcome=value + (", by default" if by_default and value != "Unknown" else ""), answer=a)
        if isinstance(x, lf.Extreme):
            a = comparison.extreme(self.db, self.ctx, x.pred)
            return Result(*head, outcome=report.extreme_text(self.db, a), answer=a)
        if isinstance(x, lf.Describe):
            return Result(*head, outcome=report.describe(self.db, self.ctx, x.entity.id))
        prior = store.repeat_of(self.db, printed, self.ctx)
        if prior:
            return Result(*head, outcome=f'already told: "{prior[1]}"')
        if isinstance(x, lf.Same):
            if self.ctx != "world":
                return Result(*head, outcome="refused: identity inside a supposition is not stored yet")
            sid = store.add_sentence(self.db, text, printed, self.ctx, trust, observation)
            store.merge(self.db, x.a, x.b, sid)
            history.add_mentions(self.db, sid, [(0, x.a.id, "sg"), (1, x.b.id, "sg")])
            self._derive()
            return Result(*head, outcome=f"one thing: {x.a.id} and {x.b.id}")
        if isinstance(x, lf.Rule):
            if self.ctx != "world":
                return Result(*head, outcome="refused: a rule inside a supposition is not stored yet")
            refusal = negation.check(self.db, x)
            if refusal is not None:
                return Result(*head, outcome=lf.show(refusal))
            sid = store.add_sentence(self.db, text, printed, self.ctx, trust, observation)
            store.add_rule(self.db, x, sid)
            words.remember(self.db, x, sid)
            history.add_mentions(self.db, sid, [m for m in x.mentions if not m[1].startswith("~")])
            self._derive()
            return Result(*head, outcome="rule stored")
        if x.claims and self.ctx != "world":
            return Result(*head, outcome="refused: a claim inside a supposition is not stored yet")
        for pred in {a.pred for a in x.atoms if a.pred.startswith(PREFIX)}:
            comparison.ensure_axioms(self.db, pred)
        if any(a.pred in (lf.BEFORE, "_in_p_temp") for a in x.atoms):
            ordering.ensure_time_axioms(self.db)
            x = ordering.reuse_events(self.db, x, self.ctx)
        sid = store.add_sentence(self.db, text, printed, self.ctx, trust, observation)
        anon_before = store.fresh_of_kind(self.db, "anon")
        claims_before = store.fresh_of_kind(self.db, "claim")
        stored = store.tell(self.db, x, sid, self.ctx, allow_conflict=observation)
        if isinstance(stored, lf.Refusal):
            opposite = prove(self.db, int(stored.detail))
            return Result(*head, outcome=f"refused, contradicts:\n{say.proof_text(self.db, opposite)}")
        words.remember(self.db, x, sid)
        for claim_id, (ref, content) in zip(store.fresh_of_kind(self.db, "claim")[len(claims_before):], x.claims):
            # The clause holds in a context apart that the world does not inherit and the engine does not derive in.
            inner = store.tell(self.db, lf.Tell(content), sid, claim_id, allow_conflict=True)
            self.db.execute("INSERT INTO claim(id, printed, sentence) VALUES (?, ?, ?)", (claim_id, claims.claim_key(content), sid))
        new = store.fresh_of_kind(self.db, "anon")[len(anon_before):]
        # The store numbers new things in the order the atoms first mention them.
        local = list(dict.fromkeys(t.id for a in x.atoms for t in a.args if isinstance(t, lf.Const) and t.kind == "anon"))
        stored_id = dict(zip(local, new))
        history.add_mentions(self.db, sid, [(pos, stored_id.get(i[1:], i) if i.startswith("~") else i, num) for pos, i, num in x.mentions
                                          if not i.startswith("~") or i[1:] in stored_id])
        self._derive()
        return Result(*head, outcome=f"stored, {len(stored)} new fact(s)")

    def suppose(self, text: str) -> Result:
        """Store a statement in a new context that inherits the world. Questions see both until drop()."""
        if self.ctx != "world":
            raise ValueError("a supposition inside a supposition is not supported")
        self._suppositions += 1
        # The engine's round bookkeeping is state too; drop puts it back.
        self._ran = self.db.execute("SELECT id, ran FROM rule").fetchall()
        self.ctx = f"s{self._suppositions}"
        return self.hear(text)

    def drop(self) -> None:
        if self.ctx == "world":
            raise ValueError("there is no supposition to drop")
        store.drop_ctx(self.db, self.ctx)
        self.db.executemany("UPDATE rule SET ran = ? WHERE id = ?", [(ran, rid) for rid, ran in self._ran])
        self.ctx = "world"

    def propose(self) -> list[Proposal]:
        return proposals.propose(self.db)

    def confirm(self, proposal: Proposal) -> Result:
        """Store the proposed rule, with the confirmed question as its source."""
        sid = store.add_sentence(self.db, proposal.question + " (confirmed)")
        rule = lf.Rule((Atom(proposal.q_pred, (Var("x"),)),), (Atom(proposal.p_pred, (Var("x"),)),))
        store.add_rule(self.db, rule, sid)
        self._derive()
        return Result(0, 0, lf.show(rule), "rule stored")

    def tell(self, text: str, trust: int = 0) -> Result:
        return self.hear(text, trust)

    def ask(self, text: str) -> Result:
        return self.hear(text)

    def _history(self) -> list[tuple[int, str, str]]:
        return history.recent_mentions(self.db)

    def _lookup(self, pred: str) -> set[str]:
        return store.things_with(self.db, pred, self.ctx)
