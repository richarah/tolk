"""The state a reading is compiled in: which variables are bound how, and which become constants."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from tolk import lf
from tolk.lf import Const, Var
from tolk.rules import quant
from tolk.sem import EP

Lookup = Callable[[str], set[str]]


@dataclass
class Ctx:
    mode: str  # ask, tell or rule
    side: str  # where the atoms being mapped go: tell, ask, head or body
    bound: dict[str, str]
    alias: dict[str, str]
    const: dict[str, str]
    negated: set[str]
    usage: Counter
    fresh: dict[str, Const] = field(default_factory=dict)
    counts: Counter = field(default_factory=Counter)
    compared: dict[str, EP] = field(default_factory=dict)  # an adjective's event to the more_comp that compares it
    claim: dict[str, "lf.Const | lf.Var"] = field(default_factory=dict)  # a clause-verb's hole to the claim it stands for
    marked: set[str] = field(default_factory=set)  # events with a tense, a modal or a progressive of their own: past, future, can, prog

    def term(self, var: str) -> Const | Var:
        while var in self.alias:
            var = self.alias[var]
        if var in self.const:
            return Const(self.const[var])
        if self.mode == "tell" and (Var(var).event or self.bound.get(var) == quant.INDEF):
            if var not in self.fresh:
                kind = "event" if Var(var).event else "anon"
                self.counts[kind] += 1
                self.fresh[var] = Const(lf.fresh_id(kind, self.counts[kind]), kind)
            return self.fresh[var]
        return Var(var)

    def no_event(self, ep: EP) -> Const | Var:
        """The event of a negated predication. A told or asked one is an event like any other, so that its tense, modal and progressive
        are kept on it and asked of it. In a rule body it is unknown, so negation as failure matches any event. In a rule's conclusion it
        is empty, which stands for a present event with no modal, unless the event has a tense, modal or progressive of its own: then the
        rule makes an event for it, which carries them."""
        if self.side in ("tell", "ask"):
            return self.term(ep.args["ARG0"])
        if self.side == "head":
            return self.term(ep.args["ARG0"]) if ep.args["ARG0"] in self.marked else Const("", lf.NO_EVENT)
        return Var(f"e{ep.args['ARG0']}n")
