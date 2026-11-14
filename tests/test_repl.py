import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import repl  # noqa: E402
from tolk.mind import Mind  # noqa: E402


class Breaks(Mind):
    """A Mind with a bug on one input, to show that the repl survives it."""

    def hear(self, text: str):
        if text == "Boom.":
            raise KeyError("a bug")
        return super().hear(text)


def test_an_internal_error_prints_one_line_and_the_session_continues() -> None:
    out, err = io.StringIO(), io.StringIO()
    repl.run(["Tweety is a robin.", "Boom.", "Is Tweety a robin?"], Breaks(), out, err)
    lines = out.getvalue().splitlines()
    assert "  internal error, see stderr; continuing" in lines
    assert lines.count("  internal error, see stderr; continuing") == 1
    assert "  Yes" in lines  # the sentence after the error was still answered
    assert "KeyError" in err.getvalue() and "Traceback" in err.getvalue()


def test_no_refused_or_odd_sentence_ends_the_session() -> None:
    odd = ["", "?", "Kim", "Who is Kim?", "Does Kim not like Nemo?", "Kim can sing.", "Every dog does not bark.", "Fish do not fly.", "Nobody flies."]
    out, err = io.StringIO(), io.StringIO()
    repl.run(odd, Mind(), out, err)
    assert "internal error" not in out.getvalue() and err.getvalue() == ""
