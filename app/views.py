import base64
import tempfile

from django.conf import settings
from django.shortcuts import render
from openai import OpenAI

from app.models import Conversation
from app.models import Message
from goglobal.users.models import User

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


def generate_next_response(conversation: Conversation) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant teaching someone "
                f"how to speak {conversation.language}. When responding, "
                f"keep your language simple and easy for beginners of "
                f"the {conversation.language} language. Always respond "
                f"in {conversation.language}. Keep the conversation flowing "
                f"by asking a new question at the end based on the conversation. "
                f"Only respond in a few sentences to emulate a real chat experience.",
            },
            *conversation.messages_param,
        ],
    )
    return completion.choices[0].message.content


def get_initial_conversation(user: User) -> Conversation:
    conversation, created = Conversation.objects.get_or_create(user=user)
    if created:
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="Bonjour Laura, je suis votre assistant Tristan ici pour "
            "vous apprendre "
            "le français. Pourquoi ne commences-tu pas par me parler et me dire ce que "
            "tu as fait aujourd'hui ?",
        )
    return conversation


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
