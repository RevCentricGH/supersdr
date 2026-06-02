"""DeckCopyGenerator - build the copy prompt, call Claude, and parse the result tolerantly.

The model is asked for JSON, but real models wrap it: in a ```json fence, in a bare ``` fence,
or in a sentence of prose. ``extract`` handles all three, and short-circuits on the
``INSUFFICIENT_SIGNAL`` sentinel - the product would rather refuse than ship boilerplate.
``validate`` then enforces the six keys a deck needs. The Claude client is injected as a
callable ``(prompt) -> str`` so the parsing and validation can be tested without an API key;
``anthropic_client`` builds the real one.
"""
import json
import re

from .errors import CopyValidationError, InsufficientSignalError

REQUIRED_KEYS = ("headline", "problem", "solution", "proof", "cta_text", "cta_url")
INSUFFICIENT_SIGNAL = "INSUFFICIENT_SIGNAL"

_FENCED = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)

PROMPT_TEMPLATE = """You are writing copy for a short, tailored sales deck for one prospect.
Ground every claim in the call transcript and the prospect's own website below. Do not invent
facts. If you cannot find real, specific signal about what this company does and needs, reply
with the single word {sentinel} and nothing else.

Return a JSON object with exactly these keys: {keys}.

## Prospect name
{name}

## Company
{company}

## Website
{website}

## Call transcript
{transcript}

## Website content (scraped)
{site_content}
"""


class DeckCopyGenerator:
    def __init__(self, claude, required_keys=REQUIRED_KEYS):
        self._claude = claude
        self.required_keys = tuple(required_keys)

    def build_prompt(self, prospect, transcript, site_content):
        return PROMPT_TEMPLATE.format(
            sentinel=INSUFFICIENT_SIGNAL,
            keys=", ".join(self.required_keys),
            name=prospect.get("name", ""),
            company=prospect.get("company", ""),
            website=prospect.get("website", ""),
            transcript=transcript,
            site_content=site_content,
        )

    def generate(self, prospect, transcript, site_content):
        prompt = self.build_prompt(prospect, transcript, site_content)
        raw = self._claude(prompt)
        return self.validate(self.extract(raw))

    def extract(self, raw):
        if INSUFFICIENT_SIGNAL in raw:
            raise InsufficientSignalError(
                "copy model returned INSUFFICIENT_SIGNAL; refusing to build a boilerplate deck"
            )
        fenced = _FENCED.search(raw)
        if fenced:
            return json.loads(fenced.group(1).strip())
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise CopyValidationError(list(self.required_keys))

    def validate(self, data):
        missing = [k for k in self.required_keys if k not in data]
        if missing:
            raise CopyValidationError(missing)
        return data


def anthropic_client(api_key, *, model="claude-opus-4-8", max_tokens=2000):
    """Real Claude callable. Returns the concatenated text of the model's response."""

    def call(prompt):
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    return call
