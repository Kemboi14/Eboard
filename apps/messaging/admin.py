from django.contrib import admin
from .models import Message, MessageRecipient, MessageThread


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'status', 'priority', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('subject', 'body', 'sender__email')
    ordering = ('-created_at',)
    list_per_page = 25


@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = ('message', 'recipient', 'read', 'read_at')
    list_filter = ('read', 'read_at')
    search_fields = ('recipient__email', 'message__subject')
    ordering = ('-message__created_at',)
    list_per_page = 25


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('subject', 'active', 'created_at', 'updated_at')
    list_filter = ('active', 'created_at')
    search_fields = ('subject',)
    ordering = ('-created_at',)
    list_per_page = 25
