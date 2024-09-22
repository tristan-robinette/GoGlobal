from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from openai import OpenAI

from app.ai import generate_audio_and_save
from app.ai import generate_next_response
from app.ai import get_initial_conversation
from app.ai import get_transcription_from_bs64
from app.ai import translate_text_to_english
from app.models import Message

client = OpenAI(api_key=settings.OPEN_AI_KEY)


@login_required
def index(request):
    conversation = get_initial_conversation(request.user)
    ctx = {
        "conversation": conversation,
    }
    if request.method == "POST":
        audio_data = request.POST.get("audio_data")
        user_content = request.POST.get("user_content")
        # todo handle no audio AND no user content written!
        if audio_data:
            params = {"language": request.POST.get("language")}
            user_content = get_transcription_from_bs64(audio_data, **params)
        # user message is added
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_content,
        )
        agent_response = generate_next_response(conversation=conversation)
        # Next add the assistant response.
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=agent_response,
        )
    return render(request, "pages/home.html", context=ctx)


@login_required
def transcribe(request, pk):
    message = Message.objects.filter(id=pk).first()
    if not message.audio_link:
        generate_audio_and_save(message)
    ctx = {"message": message}
    return render(request, "fragments/audio_transcription.html", context=ctx)


@login_required
def translate(request, pk):
    message = Message.objects.filter(id=pk).first()
    message = translate_text_to_english(message)
    ctx = {"message": message}
    return render(request, "fragments/message.html", context=ctx)
