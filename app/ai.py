import base64
import tempfile

from django.conf import settings
from django.core.files.base import ContentFile
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


MAX_HISTORY = 10


def generate_next_response(conversation: Conversation) -> str:
    msg_history = conversation.messages_param
    current_history = len(msg_history)
    if current_history > MAX_HISTORY:
        offset = current_history - MAX_HISTORY
        msg_history = msg_history[offset:]
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
            *msg_history,
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


def generate_audio_and_save(message: Message):
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=message.content,
    ) as response:
        audio_content = ContentFile(b"")
        for chunk in response.iter_bytes():
            audio_content.write(chunk)
    message.audio_link.save(f"audio_{message.id}.mp3", audio_content)
    message.save()
    return message


def translate_text_to_english(message: Message) -> Message:
    if message.english_translation:
        return message
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert translater. "
                "Give me back the text in English.",
            },
            {"role": "user", "content": message.content},
        ],
    )
    message.english_translation = completion.choices[0].message.content
    message.save()
    return message
