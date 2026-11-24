"""The mark of an event: its tense, and its modal or progressive, as the tense and modal facts about it record them. A negative fact
contradicts a positive one only if their events have the same mark: "Kim did not sing." contradicts "Kim sang.", but not "Kim sings."
or "Kim can sing.". An empty event (a negative fact a rule derives) has the mark of a present event with no modal."""

from tolk import lf

# A predicate whose first argument is an event: a verb, adjective or preposition. A noun's first argument is the thing itself.
EVENT_FIRST = "{alias}.pred GLOB '_*' AND {alias}.pred NOT GLOB '_*_n_*'"


def takes_event(pred: str) -> bool:
    return pred.startswith("_") and "_n_" not in pred[1:]


def sql(col: str) -> str:
    """SQL for the mark of the event in `col`: tense, then the lowest and highest modal kind (a progressive past has two marks)."""
    def one(pred: str, agg: str) -> str:
        return f"IFNULL((SELECT {agg}(x.a1) FROM fact x WHERE x.pred = '{pred}' AND x.a0 = {col} AND x.positive = 1), '')"
    return f"({one(lf.TENSE, 'MIN')} || '/' || {one(lf.MODAL, 'MIN')} || '/' || {one(lf.MODAL, 'MAX')})"


def mark(tenses: list[str], modals: list[str]) -> str:
    """The same mark, from the tense and modal kinds of an event that is not stored yet."""
    return f"{min(tenses, default='')}/{min(modals, default='')}/{max(modals, default='')}"
