from django.contrib import admin
from notices.models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'is_pinned', 'is_active', 'created_at', 'posted_by')
    list_filter = ('audience', 'is_pinned', 'is_active')
    search_fields = ('title', 'body')
    autocomplete_fields = ('department', 'course')
