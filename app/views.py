import base64
import tempfile

from django.conf import settings
from django.shortcuts import render
from openai import OpenAI

client = OpenAI(api_key=settings.OPEN_AI_KEY)


def get_transcription_from_bs64(data: bytes, **kwargs) -> str:
    audio_file = base64.b64decode(data)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_file:
        tmp_file.write(audio_file)
        kwargs.pop("model", None)
        kwargs.pop("file", None)
        with open(tmp_file.name, "rb") as file_for_transcription:  # noqa: PTH123
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=file_for_transcription,
                **kwargs,
            )
            return transcription.text


def index(request):
    ctx = {}
    if request.method == "POST":
        audio_data = request.POST.get("audio_data")
        if audio_data:
            params = {"language": request.POST.get("language")}
            transcription = get_transcription_from_bs64(audio_data, **params)
            ctx["message"] = transcription
    return render(request, "pages/home.html", context=ctx)
