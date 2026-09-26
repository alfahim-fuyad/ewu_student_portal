from django.contrib import admin
from chatbot.models import ChatHistory


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'intent', 'is_allowed', 'created_at')
    list_filter = ('role', 'intent', 'is_allowed')
    search_fields = ('content', 'user__username')
    readonly_fields = ('metadata', 'created_at')
    date_hierarchy = 'created_at'
