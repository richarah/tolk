""""forget that ...": retract the latest statement that told the same thing."""

from tolk import history, lf


def forget(mind, target: str, result):
    """`result` is the Result class of the mind; it is passed in so this module does not import mind."""
    readings, k, x = mind._read(target)
    head = (k + 1, len(readings), lf.show(x))
    if isinstance(x, (lf.Refusal, lf.Ask, lf.Describe, lf.Every, lf.Extreme)):
        return result(*head, outcome="refused: only a statement can be forgotten")
    found = history.latest_told(mind.db, lf.show(x), mind.ctx)
    if found is None:
        return result(*head, outcome="nothing that was told means that")
    if mind.db.execute("SELECT 1 FROM merge WHERE sentence = ?", (found[0],)).fetchone():
        return result(*head, outcome="refused: an identity cannot be forgotten")
    mind._retract(found[0], f"forget that {target}")
    return result(*head, outcome=f'forgot "{found[1]}"')
