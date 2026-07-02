from pathlib import Path

from flask import current_app
from openai import OpenAI


class TranscriptionUnavailable(RuntimeError):
    pass


def transcribe_video(video_file_path, language="en"):
    key = current_app.config.get("OPENAI_API_KEY")
    if not key:
        raise TranscriptionUnavailable("OPENAI_API_KEY is not configured; paste or edit a transcript manually")
    path = Path(video_file_path)
    if path.stat().st_size > 25 * 1024 * 1024:
        raise TranscriptionUnavailable("File exceeds the hosted Whisper 25 MB request limit; pre-extract/compress audio")
    with path.open("rb") as stream:
        result = OpenAI(api_key=key).audio.transcriptions.create(model="whisper-1", file=stream, language=language)
    return result.text

