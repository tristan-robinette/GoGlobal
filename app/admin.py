from django.contrib import admin

from app.models import Conversation
from app.models import Message

admin.site.register(Conversation)
admin.site.register(Message)
