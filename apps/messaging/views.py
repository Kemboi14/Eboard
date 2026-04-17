from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Message, MessageRecipient, MessageThread, Announcement


# ─── Message Views ─────────────────────────────────────────────────────────────

class MessageListView(LoginRequiredMixin, ListView):
    """List messages for the current user"""
    model = Message
    template_name = 'messages/messages.html'
    context_object_name = 'messages'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Show sent and received messages
        queryset = queryset.filter(
            Q(sender=user) | Q(recipients=user)
        ).distinct()
        
        # Filter by folder
        folder = self.request.GET.get('folder', 'inbox')
        if folder == 'sent':
            queryset = queryset.filter(sender=user)
        elif folder == 'inbox':
            queryset = queryset.filter(recipients=user)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Count unread messages
        unread_count = MessageRecipient.objects.filter(
            recipient=user,
            read=False
        ).count()
        context['unread_count'] = unread_count
        
        return context


class MessageDetailView(LoginRequiredMixin, DetailView):
    """View message details"""
    model = Message
    template_name = 'messages/message_detail.html'
    context_object_name = 'message'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        return queryset.filter(
            Q(sender=user) | Q(recipients=user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message = self.object
        user = self.request.user
        
        # Mark as read if user is a recipient
        recipient = MessageRecipient.objects.filter(
            message=message,
            recipient=user
        ).first()
        if recipient:
            recipient.mark_as_read()
        
        context['recipient_status'] = recipient
        return context


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Create a new message"""
    model = Message
    template_name = 'messages/message_form.html'
    fields = ['subject', 'body', 'priority', 'recipients', 'attachments', 'related_meeting', 'related_motion']
    success_url = reverse_lazy('messaging:messages')
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.status = 'sent'
        form.instance.sent_at = timezone.now()
        message = form.save()
        
        # Create message recipient records
        for recipient in form.cleaned_data['recipients']:
            MessageRecipient.objects.create(
                message=message,
                recipient=recipient,
                received_at=timezone.now()
            )
        
        messages.success(self.request, 'Message sent successfully.')
        return super().form_valid(form)


@login_required
@require_POST
def mark_message_read(request, pk):
    """Mark a message as read"""
    message = get_object_or_404(Message, pk=pk)
    recipient = MessageRecipient.objects.filter(
        message=message,
        recipient=request.user
    ).first()
    
    if recipient:
        recipient.mark_as_read()
        messages.success(request, 'Message marked as read.')
    
    return redirect('messaging:message_detail', pk=pk)


@login_required
@require_POST
def delete_message(request, pk):
    """Delete a message"""
    message = get_object_or_404(Message, pk=pk)
    
    if message.sender != request.user and request.user not in message.recipients.all():
        messages.error(request, "You don't have permission to delete this message.")
        return redirect('messaging:messages')
    
    message.status = 'archived'
    message.save()
    
    messages.success(request, 'Message archived.')
    return redirect('messaging:messages')


# ─── Message Thread Views ─────────────────────────────────────────────────────

class MessageThreadListView(LoginRequiredMixin, ListView):
    """List message threads"""
    model = MessageThread
    template_name = 'messages/threads.html'
    context_object_name = 'threads'
    ordering = ['-last_message_at', '-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            participants=self.request.user,
            active=True
        )
        return queryset


class MessageThreadDetailView(LoginRequiredMixin, DetailView):
    """View message thread details"""
    model = MessageThread
    template_name = 'messages/thread_detail.html'
    context_object_name = 'thread'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.object
        context['messages'] = thread.original_message.threads.all() if thread.original_message else []
        return context


# ─── Announcement Views ───────────────────────────────────────────────────────

class AnnouncementListView(LoginRequiredMixin, ListView):
    """List announcements"""
    model = Announcement
    template_name = 'messages/announcements.html'
    context_object_name = 'announcements'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.GET.get('status', 'published')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    """View announcement details"""
    model = Announcement
    template_name = 'messages/announcement_detail.html'
    context_object_name = 'announcement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcement = self.object
        
        # Mark as viewed
        announcement.mark_viewed(self.request.user)
        
        return context


class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """Create a new announcement"""
    model = Announcement
    template_name = 'messages/announcement_form.html'
    fields = ['title', 'content', 'summary', 'target_audience', 'custom_targets', 'priority', 'publish_at', 'expire_at', 'attachments', 'related_meeting', 'related_motion']
    success_url = reverse_lazy('messaging:announcements')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = 'draft'
        messages.success(self.request, 'Announcement created successfully.')
        return super().form_valid(form)


@login_required
@require_POST
def publish_announcement(request, pk):
    """Publish an announcement"""
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if announcement.created_by != request.user and request.user.role not in ['it_administrator', 'company_secretary']:
        messages.error(request, "You don't have permission to publish this announcement.")
        return redirect('messaging:announcement_detail', pk=pk)
    
    announcement.publish()
    messages.success(request, 'Announcement published successfully.')
    return redirect('messaging:announcement_detail', pk=pk)


@login_required
@require_POST
def archive_announcement(request, pk):
    """Archive an announcement"""
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if announcement.created_by != request.user and request.user.role not in ['it_administrator', 'company_secretary']:
        messages.error(request, "You don't have permission to archive this announcement.")
        return redirect('messaging:announcement_detail', pk=pk)
    
    announcement.archive()
    messages.success(request, 'Announcement archived.')
    return redirect('messaging:announcement_detail', pk=pk)
