from django.urls import path

from app import views

urlpatterns = [
    path("", views.index, name="app"),
    path("transcribe/<int:pk>", views.transcribe, name="transcribe"),
    path("translate/<int:pk>", views.translate, name="translate"),
]
