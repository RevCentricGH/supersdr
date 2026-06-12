"""Transcriber - Deepgram primary, Groq fallback.

``transcribe(audio_url) -> str`` calls Deepgram first. Groq is invoked if and only if
Deepgram comes back empty (None, empty, or whitespace-only) or raises. If both come back
empty or raise, a ``TranscriptionError`` is raised rather than returning a silent empty
string - a downstream deck built on no transcript is worse than a clear failure.

The two providers are injected as callables ``(audio_url) -> str | None``. The
``deepgram_provider`` / ``groq_provider`` factories below build the real, requests-based
callables from an API key; they are kept thin and validated by the manual end-to-end run,
not unit-tested for transport detail.
"""
from .errors import TranscriptionError


def _is_empty(text):
    return text is None or not str(text).strip()


class Transcriber:
    def __init__(self, deepgram, groq):
        self._deepgram = deepgram
        self._groq = groq

    def transcribe(self, audio_url):
        primary = self._safe_call(self._deepgram, audio_url)
        if not _is_empty(primary):
            return primary
        fallback = self._safe_call(self._groq, audio_url)
        if not _is_empty(fallback):
            return fallback
        raise TranscriptionError(
            f"both Deepgram and Groq returned no transcript for {audio_url}"
        )

    @staticmethod
    def _safe_call(provider, audio_url):
        try:
            return provider(audio_url)
        except Exception:
            return None


def deepgram_provider(api_key, *, transport=None, model="nova-2"):
    """Real Deepgram pre-recorded transcription callable. Posts the audio URL and pulls the
    first alternative's transcript out of the response."""
    transport = transport or _default_transport()

    def transcribe(audio_url):
        url = f"https://api.deepgram.com/v1/listen?model={model}&smart_format=true"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }
        data = transport("POST", url, headers, {"url": audio_url}).json()
        channels = (data.get("results") or {}).get("channels") or []
        if not channels:
            return ""
        alts = channels[0].get("alternatives") or []
        return alts[0].get("transcript", "") if alts else ""

    return transcribe


def groq_provider(api_key, *, transport=None, model="whisper-large-v3"):
    """Real Groq transcription callable. Groq's audio endpoint takes the file, so the URL is
    fetched first and the bytes posted as multipart."""
    transport = transport or _default_transport()

    def transcribe(audio_url):
        audio_bytes = transport("GET", audio_url, {}, None).content
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = transport(
            "POST",
            url,
            headers,
            None,
            files={"file": ("audio", audio_bytes)},
            data={"model": model, "response_format": "text"},
        )
        text = resp.text
        return text.strip() if text else ""

    return transcribe


def _default_transport():
    def transport(method, url, headers, json, **kwargs):
        import requests

        return requests.request(
            method, url, headers=headers, json=json, timeout=120, **kwargs
        )

    return transport
