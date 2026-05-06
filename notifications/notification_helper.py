"""
Universal Notification Helper
Provides a robust notification system that can be used across all modules
"""
from typing import List, Optional, Dict, Any
from .services import NotificationService
import logging

logger = logging.getLogger(__name__)


class UniversalNotificationHelper:
    """
    Universal notification helper that can be used across all modules.
    Provides a consistent interface for sending notifications.
    """
    
    @staticmethod
    def send_notification(
        school_id: Optional[int],
        notification_type: str,
        title: str,
        message: str,
        recipient_user_ids: List[int],
        created_by_user_id: int,
        target_url: Optional[str] = None,
        target_module: Optional[str] = None,
        target_record_id: Optional[int] = None,
        expires_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a notification to specified users.
        
        Args:
            school_id: School ID (None for Super Admin/Support Executive)
            notification_type: Type of notification (e.g., 'TicketCreated', 'FeeReminder')
            title: Notification title
            message: Notification message
            recipient_user_ids: List of user IDs to receive the notification
            created_by_user_id: User ID who created the notification
            target_url: Optional URL to navigate when notification is clicked
            target_module: Optional module name (e.g., 'tickets', 'fees')
            target_record_id: Optional record ID related to the notification
            expires_at: Optional expiration datetime
            
        Returns:
            Dict with success status and notification_id
        """
        try:
            # Filter out invalid recipient IDs
            valid_recipients = [uid for uid in recipient_user_ids if uid and uid > 0]
            
            if not valid_recipients:
                logger.warning(f"No valid recipients for notification: {title}")
                return {'success': False, 'error': 'No valid recipients'}
            
            result = NotificationService.create_notification(
                school_id=school_id,
                type_name=notification_type,
                title=title,
                message=message,
                recipient_user_ids=valid_recipients,
                created_by_user_id=created_by_user_id,
                target_url=target_url,
                target_module=target_module,
                target_record_id=target_record_id,
                expires_at=expires_at
            )
            
            if result.get('success'):
                logger.info(f"Notification sent: {title} to {len(valid_recipients)} users")
            else:
                logger.error(f"Failed to send notification: {result.get('status')}")
            
            return result
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== TICKET NOTIFICATIONS ====================
    
    @staticmethod
    def notify_ticket_created(ticket_id: int, ticket_number: str, subject: str, 
                             school_id: int, created_by: int, notify_admins: bool = True):
        """Notify when a ticket is created"""
        if not notify_admins:
            return {'success': False, 'error': 'No recipients specified'}
        
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                # Get Super Admin user IDs
                cursor.execute("""
                    SELECT u.UserID FROM UserMaster u
                    INNER JOIN ProfileMaster p ON u.ProfileID = p.ProfileID
                    WHERE p.ProfileName = 'Super Admin' AND u.IsActive = 1 AND ISNULL(u.IsDeleted, 0) = 0
                """)
                admin_ids = [row[0] for row in cursor.fetchall()]
                
                if admin_ids:
                    return UniversalNotificationHelper.send_notification(
                        school_id=school_id,
                        notification_type='TicketCreated',
                        title=f'New Ticket: {ticket_number}',
                        message=f'Ticket "{subject}" has been created.',
                        recipient_user_ids=admin_ids,
                        created_by_user_id=created_by,
                        target_url=f'/tickets/view/{ticket_id}/',
                        target_module='tickets',
                        target_record_id=ticket_id
                    )
        except Exception as e:
            logger.error(f"Error in notify_ticket_created: {str(e)}")
        
        return {'success': False, 'error': 'Failed to notify'}
    
    @staticmethod
    def notify_ticket_assigned(ticket_id: int, ticket_number: str, subject: str,
                              school_id: int, assigned_by: int, assigned_to: int):
        """Notify when a ticket is assigned"""
        from core.url_encryption import encrypt_id
        token = encrypt_id(ticket_id)
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='TicketAssigned',
            title=f'Ticket Assigned: {ticket_number}',
            message=f'Ticket "{subject}" has been assigned to you.',
            recipient_user_ids=[assigned_to],
            created_by_user_id=assigned_by,
            target_url=f'/tickets/view/{token}/',
            target_module='tickets',
            target_record_id=ticket_id
        )
    
    @staticmethod
    def notify_ticket_status_changed(ticket_id: int, ticket_number: str, subject: str,
                                    new_status: str, school_id: int, changed_by: int,
                                    creator_id: int, assigned_to_id: Optional[int] = None):
        """Notify when ticket status changes"""
        from core.url_encryption import encrypt_id
        
        recipients = []
        if creator_id and creator_id != changed_by:
            recipients.append(creator_id)
        if assigned_to_id and assigned_to_id != changed_by:
            recipients.append(assigned_to_id)
        
        if not recipients:
            return {'success': False, 'error': 'No recipients'}
        
        token = encrypt_id(ticket_id)
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='TicketStatusChanged',
            title=f'Ticket Status Updated: {ticket_number}',
            message=f'Ticket "{subject}" status changed to {new_status}.',
            recipient_user_ids=recipients,
            created_by_user_id=changed_by,
            target_url=f'/tickets/view/{token}/',
            target_module='tickets',
            target_record_id=ticket_id
        )
    
    @staticmethod
    def notify_ticket_message(ticket_id: int, ticket_number: str, message: str,
                            school_id: int, sender_id: int, creator_id: int,
                            assigned_to_id: Optional[int] = None):
        """Notify when a message is added to a ticket"""
        from core.url_encryption import encrypt_id
        
        recipients = []
        if creator_id and creator_id != sender_id:
            recipients.append(creator_id)
        if assigned_to_id and assigned_to_id != sender_id:
            recipients.append(assigned_to_id)
        
        if not recipients:
            return {'success': False, 'error': 'No recipients'}
        
        token = encrypt_id(ticket_id)
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='TicketChatMessage',
            title=f'New message on {ticket_number}',
            message=message[:100] + '...' if len(message) > 100 else message,
            recipient_user_ids=recipients,
            created_by_user_id=sender_id,
            target_url=f'/tickets/view/{token}/#chat',
            target_module='tickets',
            target_record_id=ticket_id
        )
    
    # ==================== FEE NOTIFICATIONS ====================
    
    @staticmethod
    def notify_fee_payment_received(student_id: int, student_name: str, amount: float,
                                   school_id: int, recipient_ids: List[int]):
        """Notify when fee payment is received"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='FeePaymentConfirmed',
            title='Fee Payment Received',
            message=f'Fee payment of ₹{amount} received for {student_name}.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/fees/',
            target_module='fees',
            target_record_id=student_id
        )
    
    @staticmethod
    def notify_fee_reminder(student_id: int, student_name: str, fee_type: str,
                          amount: float, due_date: str, school_id: int, recipient_ids: List[int]):
        """Notify fee payment reminder"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='FeeReminder',
            title='Fee Payment Reminder',
            message=f'{fee_type} of ₹{amount} is due on {due_date} for {student_name}.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/fees/',
            target_module='fees',
            target_record_id=student_id
        )
    
    @staticmethod
    def notify_fee_overdue(student_id: int, student_name: str, fee_type: str,
                         amount: float, school_id: int, recipient_ids: List[int]):
        """Notify when fee is overdue"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='FeeDueDate',
            title='Fee Overdue Alert',
            message=f'{fee_type} of ₹{amount} is overdue for {student_name}.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/fees/',
            target_module='fees',
            target_record_id=student_id
        )
    
    # ==================== ATTENDANCE NOTIFICATIONS ====================
    
    @staticmethod
    def notify_attendance_low(student_id: int, student_name: str, attendance_percentage: float,
                            school_id: int, recipient_ids: List[int]):
        """Notify when attendance is low"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='AttendanceLow',
            title='Low Attendance Alert',
            message=f'{student_name} attendance has dropped to {attendance_percentage}%.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/attendance/',
            target_module='attendance',
            target_record_id=student_id
        )
    
    @staticmethod
    def notify_attendance_summary(school_id: int, date: str, present: int, absent: int,
                                 recipient_ids: List[int]):
        """Notify daily attendance summary"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='AttendanceSummary',
            title='Daily Attendance Summary',
            message=f'Attendance for {date}: {present} present, {absent} absent.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/attendance/',
            target_module='attendance'
        )
    
    # ==================== EXAM NOTIFICATIONS ====================
    
    @staticmethod
    def notify_exam_scheduled(exam_id: int, exam_name: str, exam_date: str,
                            school_id: int, recipient_ids: List[int]):
        """Notify when exam is scheduled"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='ExamScheduled',
            title='Exam Scheduled',
            message=f'{exam_name} has been scheduled for {exam_date}.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/exams/',
            target_module='exams',
            target_record_id=exam_id
        )
    
    @staticmethod
    def notify_exam_result_published(exam_id: int, exam_name: str, student_id: int,
                                    school_id: int, recipient_ids: List[int]):
        """Notify when exam results are published"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='ExamResultPublished',
            title='Exam Results Published',
            message=f'Results for {exam_name} have been published.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url=f'/exams/results/{exam_id}/',
            target_module='exams',
            target_record_id=exam_id
        )
    
    # ==================== TIMETABLE NOTIFICATIONS ====================
    
    @staticmethod
    def notify_timetable_released(class_id: int, class_name: str, school_id: int,
                                 recipient_ids: List[int]):
        """Notify when timetable is released"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='TimetableReleased',
            title='Timetable Released',
            message=f'Timetable for {class_name} has been released.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/timetable/',
            target_module='timetable',
            target_record_id=class_id
        )
    
    @staticmethod
    def notify_timetable_updated(class_id: int, class_name: str, school_id: int,
                                recipient_ids: List[int]):
        """Notify when timetable is updated"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='TimetableUpdated',
            title='Timetable Updated',
            message=f'Timetable for {class_name} has been updated.',
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_url='/timetable/',
            target_module='timetable',
            target_record_id=class_id
        )
    
    # ==================== GENERAL NOTIFICATIONS ====================
    
    @staticmethod
    def notify_announcement(title: str, message: str, school_id: int,
                          recipient_ids: List[int], created_by: int):
        """Send general announcement"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='GeneralAnnouncement',
            title=title,
            message=message,
            recipient_user_ids=recipient_ids,
            created_by_user_id=created_by,
            target_module='general'
        )
    
    @staticmethod
    def notify_system_alert(title: str, message: str, school_id: int,
                          recipient_ids: List[int]):
        """Send system alert"""
        return UniversalNotificationHelper.send_notification(
            school_id=school_id,
            notification_type='SystemAlert',
            title=title,
            message=message,
            recipient_user_ids=recipient_ids,
            created_by_user_id=1,
            target_module='system'
        )
