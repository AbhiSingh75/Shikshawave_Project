"""
Ticket Module - Notification Integration
Add these imports and calls to tickets/services.py
"""

from notifications.services import NotificationHelper

# Example integration points:

def integrate_ticket_created_notification(ticket_id, ticket_number, subject, school_id, created_by, assigned_to):
    """Call after ticket creation"""
    if assigned_to:
        NotificationHelper.notify_ticket_created(
            ticket_id=ticket_id,
            ticket_number=ticket_number,
            subject=subject,
            school_id=school_id,
            created_by=created_by,
            assigned_to=assigned_to
        )

def integrate_ticket_chat_notification(ticket_id, ticket_number, message, school_id, sender_id, ticket_participants):
    """Call after adding a comment"""
    # Get all participants except sender
    recipient_ids = [p for p in ticket_participants if p != sender_id]
    
    if recipient_ids:
        NotificationHelper.notify_ticket_chat_message(
            ticket_id=ticket_id,
            ticket_number=ticket_number,
            message=message,
            school_id=school_id,
            sender_id=sender_id,
            recipient_ids=recipient_ids
        )

# Add to TicketService.create_ticket() after successful creation:
"""
if result['success']:
    ticket_id = result['ticket_id']
    # ... existing code ...
    
    # Send notification
    if assigned_to_user_id:
        from notifications.services import NotificationHelper
        NotificationHelper.notify_ticket_created(
            ticket_id=ticket_id,
            ticket_number=ticket_number,
            subject=subject,
            school_id=school_id,
            created_by=user_id,
            assigned_to=assigned_to_user_id
        )
"""

# Add to TicketService.add_comment() after successful comment:
"""
if result['success']:
    # ... existing code ...
    
    # Send notification to ticket participants
    from notifications.services import NotificationHelper
    from django.db import connection
    
    # Get ticket details
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT TicketNumber, SchoolID, CreatedByUserID, AssignedToUserID
            FROM TicketMaster
            WHERE TicketID = %s
        ''', [ticket_id])
        ticket_row = cursor.fetchone()
        
        if ticket_row:
            ticket_number, school_id, creator_id, assigned_id = ticket_row
            
            # Build recipient list (exclude sender)
            recipients = []
            if creator_id and creator_id != user_id:
                recipients.append(creator_id)
            if assigned_id and assigned_id != user_id:
                recipients.append(assigned_id)
            
            if recipients:
                NotificationHelper.notify_ticket_chat_message(
                    ticket_id=ticket_id,
                    ticket_number=ticket_number,
                    message=comment_text,
                    school_id=school_id,
                    sender_id=user_id,
                    recipient_ids=recipients
                )
"""
