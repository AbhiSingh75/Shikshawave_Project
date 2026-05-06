from django.db import connection
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service layer for notification operations"""
    
    @staticmethod
    def create_notification(
        school_id: Optional[int],
        type_name: str,
        title: str,
        message: str,
        recipient_user_ids: List[int],
        created_by_user_id: int,
        target_url: Optional[str] = None,
        target_module: Optional[str] = None,
        target_record_id: Optional[int] = None,
        expires_at: Optional[str] = None
    ) -> Dict:
        """Create a notification and send to recipients"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Notification_Create"(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, [
                    school_id,
                    type_name,
                    title,
                    message,
                    target_url,
                    target_module,
                    target_record_id,
                    created_by_user_id,
                    ','.join(map(str, recipient_user_ids)),
                    expires_at
                ])
                result = cursor.fetchone()
                return {
                    'notification_id': result[0],
                    'status': result[1],
                    'success': result[0] > 0
                }
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return {'notification_id': 0, 'status': str(e), 'success': False}
    
    @staticmethod
    def get_notifications(
        user_id: int,
        school_id: int,
        page_number: int = 1,
        page_size: int = 20,
        unread_only: bool = False
    ) -> Dict:
        """Get paginated notifications for a user"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Notification_GetList"(
                        %s, %s, %s, %s, %s
                    )
                """, [user_id, school_id, page_number, page_size, 1 if unread_only else 0])
                
                columns = [col[0] for col in cursor.description]
                notifications = []
                total_count = 0
                
                for row in cursor.fetchall():
                    notification = dict(zip(columns, row))
                    notifications.append(notification)
                    # Convert TotalCount to int explicitly to avoid decimal/long issues
                    total_count = int(notification.get('TotalCount', 0))
                
                return {
                    'notifications': notifications,
                    'total_count': total_count,
                    'page_number': int(page_number),
                    'page_size': int(page_size),
                    'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0
                }
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            return {'notifications': [], 'total_count': 0, 'page_number': 1, 'page_size': page_size, 'total_pages': 0}
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Notification_MarkRead"(%s, %s)
                """, [notification_id, user_id])
                result = cursor.fetchone()
                return result[0] > 0 if result else False
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    @staticmethod
    def mark_all_as_read(user_id: int, school_id: int) -> bool:
        """Mark all notifications as read for a user"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Notification_MarkAllRead"(%s, %s)
                """, [user_id, school_id])
                result = cursor.fetchone()
                return result[0] > 0 if result else False
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return False
    
    @staticmethod
    def get_unread_count(user_id: int, school_id: int) -> int:
        """Get unread notification count"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Notification_GetUnreadCount"(%s, %s)
                """, [user_id, school_id])
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0


# Helper functions for specific notification types
class NotificationHelper:
    """Helper functions to create specific notification types"""
    
    @staticmethod
    def notify_ticket_created(ticket_id: int, ticket_number: str, subject: str, school_id: int, created_by: int, assigned_to: int):
        """Notify when a ticket is created"""
        return NotificationService.create_notification(
            school_id=school_id,
            type_name='TicketCreated',
            title=f'New Ticket: {ticket_number}',
            message=f'Ticket "{subject}" has been created and assigned to you.',
            recipient_user_ids=[assigned_to],
            created_by_user_id=created_by,
            target_url=f'/tickets/view/{ticket_id}/',
            target_module='tickets',
            target_record_id=ticket_id
        )
    
    @staticmethod
    def notify_ticket_chat_message(ticket_id: int, ticket_number: str, message: str, school_id: int, sender_id: int, recipient_ids: List[int]):
        """Notify when a chat message is received"""
        return NotificationService.create_notification(
            school_id=school_id,
            type_name='TicketChatMessage',
            title=f'New message on {ticket_number}',
            message=message[:100] + '...' if len(message) > 100 else message,
            recipient_user_ids=recipient_ids,
            created_by_user_id=sender_id,
            target_url=f'/tickets/view/{ticket_id}/#chat',
            target_module='tickets',
            target_record_id=ticket_id
        )
    
    @staticmethod
    def notify_fee_reminder(student_id: int, fee_type: str, amount: float, due_date: str, school_id: int, recipient_ids: List[int]):
        """Notify fee payment reminder"""
        return NotificationService.create_notification(
            school_id=school_id,
            type_name='FeeReminder',
            title='Fee Payment Reminder',
            message=f'{fee_type} of ₹{amount} is due on {due_date}.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/fees/',
            target_module='fees',
            target_record_id=student_id
        )
    
    @staticmethod
    def notify_attendance_low(student_id: int, attendance_percentage: float, school_id: int, recipient_ids: List[int]):
        """Notify low attendance"""
        return NotificationService.create_notification(
            school_id=school_id,
            type_name='AttendanceLow',
            title='Low Attendance Alert',
            message=f'Attendance has dropped to {attendance_percentage}%. Please take necessary action.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/attendance/',
            target_module='attendance',
            target_record_id=student_id
        )
