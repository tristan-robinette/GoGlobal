from django.db import models

from goglobal.users.models import User


class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=50, default="fr")

    def __str__(self):
        return self.user.email

    @property
    def messages_param(self):
        return [message.as_message for message in self.messages.all()]


class Message(models.Model):
    class RoleOptions(models.TextChoices):
        SYSTEM = "system", "system"
        USER = "user", "user"
        ASSISTANT = "assistant", "assistant"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=50, choices=RoleOptions.choices)
    audio_link = models.FileField(upload_to="audio/", null=True, blank=True)
    content = models.TextField()
    english_translation = models.TextField(blank=True, default="")
    created_at = models.DateField(auto_now=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return self.role

    @property
    def as_message(self):
        return {"role": self.role, "content": self.content}
