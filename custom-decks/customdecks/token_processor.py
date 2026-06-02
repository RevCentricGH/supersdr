"""TokenProcessor - per-token character budget and line-wrap.

Pure text transforms. ``truncate`` caps a token at ``char_budget`` and records every cut so
the excess is never silently dropped (it is appended to ``truncations`` and passed to the
optional ``logger``). ``wrap`` reflows text to ``line_width``. ``process`` runs both over a
token map and returns a new map, leaving the input untouched.
"""
import textwrap


class TokenProcessor:
    def __init__(self, char_budget, line_width, logger=None):
        self.char_budget = char_budget
        self.line_width = line_width
        self._logger = logger
        self.truncations = []

    def truncate(self, text, key=None):
        if len(text) <= self.char_budget:
            return text
        dropped = text[self.char_budget :]
        self.truncations.append((key, dropped))
        if self._logger:
            self._logger(
                f"TokenProcessor truncated {key or 'token'}: "
                f"dropped {len(dropped)} char(s) over budget {self.char_budget}"
            )
        return text[: self.char_budget]

    def wrap(self, text):
        if not text:
            return text
        lines = textwrap.wrap(text, self.line_width, break_long_words=True, break_on_hyphens=False)
        return "\n".join(lines)

    def process(self, tokens):
        # Reset per call so reusing one processor across decks (batch/queue mode) does not
        # accumulate truncation records from earlier decks.
        self.truncations = []
        return {key: self.wrap(self.truncate(value, key)) for key, value in tokens.items()}
