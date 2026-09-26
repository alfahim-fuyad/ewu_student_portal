"""
Chat history model — one row per chat turn so we can resume conversations.
"""
from django.conf import settings
from django.db import models


class ChatHistory(models.Model):
    """A single Q/A exchange between a user and the AI assistant."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_history',
        null=True, blank=True,  # null when bot replies before auth in tests
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True, help_text='Detected intent tag.')
    is_allowed = models.BooleanField(default=True, help_text='Whether permission check passed.')
    metadata = models.JSONField(default=dict, blank=True, help_text='Extra context for debugging.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'chat history'
        verbose_name_plural = 'chat histories'

    def __str__(self):
        return f'[{self.role}] {self.content[:80]}'
