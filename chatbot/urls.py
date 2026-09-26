"""URL routes for the chatbot app."""
from django.urls import path
from chatbot.views import chat, history, clear

app_name = 'chatbot'

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('history/', history, name='history'),
    path('clear/', clear, name='clear'),
]
