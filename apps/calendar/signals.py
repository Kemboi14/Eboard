from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from .models import CalendarEvent


def sync_calendar_event(sender, instance, created, **kwargs):
    """
    Automatically sync calendar events when source objects are created/updated.
    This function is called by specific signal handlers for each app.
    """
    try:
        # Determine event type and fields based on sender
        event_type = None
        title = ""
        description = None
        start_date = None
        end_date = None
        all_day = False
        user = None
        location = None
        status = None
        color = "#7dc143"
        
        # Meetings app
        if sender.__name__ == "Meeting":
            event_type = "meeting"
            title = instance.title
            description = instance.description
            start_date = instance.scheduled_date
            end_date = instance.end_time
            user = instance.organizer
            location = instance.location
            status = instance.status
            color = "#3b82f6"  # Blue
            
        # Voting app - Motion voting deadline
        elif sender.__name__ == "Motion":
            event_type = "voting_deadline"
            title = f"Voting Deadline: {instance.title}"
            description = instance.description
            start_date = instance.voting_deadline
            user = instance.proposed_by
            status = instance.status
            color = "#ef4444"  # Red
            
        # Documents app
        elif sender.__name__ == "Document":
            event_type = "document_due"
            title = f"Document Due: {instance.title}"
            description = instance.description
            start_date = instance.due_date
            user = instance.uploaded_by
            status = instance.status
            color = "#f59e0b"  # Orange
            
        # Risk app
        elif sender.__name__ == "Risk":
            event_type = "risk_review"
            title = f"Risk Review: {instance.title}"
            description = instance.description
            start_date = instance.next_review_date
            user = instance.owner
            status = instance.status
            color = "#8b5cf6"  # Purple
            
        # Audit app
        elif sender.__name__ == "Audit":
            event_type = "audit_date"
            title = f"Audit: {instance.title}"
            description = instance.description
            start_date = instance.scheduled_date
            user = instance.auditor
            status = instance.status
            color = "#06b6d4"  # Cyan
            
        # Organization app - Committee meetings
        elif sender.__name__ == "CommitteeMeeting":
            event_type = "committee_meeting"
            title = f"Committee Meeting: {instance.committee.name}"
            description = instance.agenda
            start_date = instance.meeting_date
            user = instance.chair
            location = instance.location
            status = instance.status
            color = "#10b981"  # Green
        
        # E-signature app
        elif sender.__name__ == "SignatureRequest":
            event_type = "esignature_deadline"
            title = f"E-Signature Deadline: {instance.document.title}"
            description = "Document awaiting signature"
            start_date = instance.deadline
            user = instance.requester
            status = instance.status
            color = "#ec4899"  # Pink
        
        # If no matching event type, skip
        if not event_type or not start_date:
            return
        
        # Get or create calendar event
        calendar_event, event_created = CalendarEvent.objects.get_or_create(
            source_app=sender.__module__.split(".")[1],
            source_model=sender.__name__,
            source_object_id=instance.id,
            defaults={
                "title": title,
                "description": description,
                "event_type": event_type,
                "start_date": start_date,
                "end_date": end_date,
                "all_day": all_day,
                "user": user,
                "location": location,
                "color": color,
                "status": status,
            }
        )
        
        # Update existing event
        if not event_created:
            calendar_event.title = title
            calendar_event.description = description
            calendar_event.event_type = event_type
            calendar_event.start_date = start_date
            calendar_event.end_date = end_date
            calendar_event.all_day = all_day
            calendar_event.user = user
            calendar_event.location = location
            calendar_event.color = color
            calendar_event.status = status
            calendar_event.save()
            
    except Exception as e:
        # Log error but don't break the signal chain
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error syncing calendar event: {str(e)}")


def delete_calendar_event(sender, instance, **kwargs):
    """
    Delete calendar event when source object is deleted.
    """
    try:
        CalendarEvent.objects.filter(
            source_app=sender.__module__.split(".")[1],
            source_model=sender.__name__,
            source_object_id=instance.id,
        ).delete()
    except Exception as e:
        # Log error but don't break the signal chain
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting calendar event: {str(e)}")


# Connect signals for each app when they're available
def connect_signals():
    """
    Connect signals for all relevant apps.
    This function is called when the calendar app is ready.
    """
    try:
        # Meetings
        from apps.meetings.models import Meeting
        post_save.connect(sync_calendar_event, sender=Meeting)
        post_delete.connect(delete_calendar_event, sender=Meeting)
    except ImportError:
        pass
    
    try:
        # Voting
        from apps.voting.models import Motion
        post_save.connect(sync_calendar_event, sender=Motion)
        post_delete.connect(delete_calendar_event, sender=Motion)
    except ImportError:
        pass
    
    try:
        # Documents
        from apps.documents.models import Document
        post_save.connect(sync_calendar_event, sender=Document)
        post_delete.connect(delete_calendar_event, sender=Document)
    except ImportError:
        pass
    
    try:
        # Risk
        from apps.risk.models import Risk
        post_save.connect(sync_calendar_event, sender=Risk)
        post_delete.connect(delete_calendar_event, sender=Risk)
    except ImportError:
        pass
    
    try:
        # Audit
        from apps.audit.models import Audit
        post_save.connect(sync_calendar_event, sender=Audit)
        post_delete.connect(delete_calendar_event, sender=Audit)
    except ImportError:
        pass
    
    try:
        # Organization
        from apps.organization.models import CommitteeMeeting
        post_save.connect(sync_calendar_event, sender=CommitteeMeeting)
        post_delete.connect(delete_calendar_event, sender=CommitteeMeeting)
    except ImportError:
        pass
    
    try:
        # E-signature
        from apps.esignature.models import SignatureRequest
        post_save.connect(sync_calendar_event, sender=SignatureRequest)
        post_delete.connect(delete_calendar_event, sender=SignatureRequest)
    except ImportError:
        pass


# Connect signals when app is ready
connect_signals()
