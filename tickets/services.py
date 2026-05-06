from django.db import connection
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TicketService:
    """Service layer for ticket operations with role validation"""

    @staticmethod
    def create_ticket(user_id, role_name, school_id, category_id, priority, subject, description, file_data=None, file_name=None, file_size=None, content_type=None, source='Website'):
        """Create a new ticket using stored procedure"""
        ticket_id = None
        ticket_number = None
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Ticket_Insert"(%s::integer, %s::varchar, %s::integer, %s::integer, %s::integer, %s::varchar, %s::text, NULL::varchar, %s::varchar)
                """, [user_id, role_name, school_id, category_id, priority, subject, description, source])
                
                result = cursor.fetchone()
                if result:
                    ticket_id, error_message = result
                    if error_message:
                        return {'success': False, 'error': error_message, 'code': 400}
                    
                    # Insert attachment if provided
                    if file_data and ticket_id:
                        cursor.execute("""
                            INSERT INTO "TicketAttachments" ("TicketID", "FileName", "FilePath", "FileData", "FileSize", "ContentType", "UploadedByUserID", "UploadedAt", "IsDeleted")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, FALSE)
                        """, [ticket_id, file_name, '', file_data, file_size, content_type, user_id])
            
            # Send notification OUTSIDE transaction
            if ticket_id:
                try:
                    from notifications.services import NotificationService
                    from core.url_encryption import encrypt_id
                    
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT "TicketNumber" FROM "TicketMaster" WHERE "TicketID" = %s', [ticket_id])
                        ticket_row = cursor.fetchone()
                        if not ticket_row:
                            return {'success': True, 'ticket_id': ticket_id, 'ticket_number': None}
                        
                        ticket_number = ticket_row[0]
                        
                        recipient_ids = []
                        
                        # Add Super Admins
                        cursor.execute("""
                            SELECT u."UserID" FROM "UserMaster" u
                            INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                            WHERE p."ProfileName" = 'Super Admin' AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                        """)
                        recipient_ids.extend([row[0] for row in cursor.fetchall()])
                        
                        # Add School Admin if ticket has SchoolID
                        if school_id:
                            cursor.execute("""
                                SELECT u."UserID" FROM "UserMaster" u
                                INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                                WHERE p."ProfileName" = 'School Admin' AND u."SchoolID" = %s AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                            """, [school_id])
                            recipient_ids.extend([row[0] for row in cursor.fetchall()])
                        
                        # Remove creator from recipients
                        recipient_ids = [uid for uid in recipient_ids if uid != user_id]
                        
                        if recipient_ids:
                            token = encrypt_id(ticket_id)
                            NotificationService.create_notification(
                                school_id=school_id,
                                type_name='TicketCreated',
                                title=f'New Ticket: {ticket_number}',
                                message=f'Ticket "{subject}" has been created.',
                                recipient_user_ids=recipient_ids,
                                created_by_user_id=user_id,
                                target_url=f'/tickets/view/{token}/',
                                target_module='tickets',
                                target_record_id=ticket_id
                            )
                except Exception as e:
                    logger.error(f"Notification error: {str(e)}")
            
            return {'success': True, 'ticket_id': ticket_id, 'ticket_number': ticket_number}
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def assign_ticket(user_id, role_name, ticket_id, assign_to_user_id, comment=None):
        """Assign ticket to support executive (Super Admin only)"""
        try:
            logger.info(f"Calling Proc_Ticket_Assign with: UserID={user_id}, RoleName={role_name}, TicketID={ticket_id}, AssignToUserID={assign_to_user_id}, Comment={comment}")
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Ticket_Assign"(%s, %s, %s, %s, %s)
                """, [user_id, role_name, ticket_id, assign_to_user_id, comment])
                
                result = cursor.fetchone()
                logger.info(f"Proc_Ticket_Assign result: {result}")
                
                if result and result[0]:
                    logger.error(f"Assignment failed: {result[0]}")
                    return {'success': False, 'error': result[0], 'code': 403}
                
                try:
                    from core.url_encryption import encrypt_id
                    from notifications.services import NotificationService
                    
                    cursor.execute('SELECT "TicketNumber", "Subject", "CreatedByUserID", "SchoolID" FROM "TicketMaster" WHERE "TicketID" = %s', [ticket_id])
                    ticket_row = cursor.fetchone()
                    if ticket_row:
                        ticket_number, subject, creator_id, school_id = ticket_row
                        token = encrypt_id(ticket_id)
                        
                        recipients = list(set([uid for uid in [creator_id, assign_to_user_id] if uid and uid != user_id]))
                        
                        if school_id:
                            cursor.execute("""
                                SELECT u."UserID" FROM "UserMaster" u
                                INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                                WHERE p."ProfileName" = 'School Admin' AND u."SchoolID" = %s AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                            """, [school_id])
                            school_admin_ids = [row[0] for row in cursor.fetchall()]
                            recipients.extend([sid for sid in school_admin_ids if sid != user_id and sid not in recipients])
                        
                        if recipients:
                            NotificationService.create_notification(
                                school_id=school_id,
                                type_name='TicketAssigned',
                                title=f'Ticket Assigned: {ticket_number}',
                                message=f'Ticket "{subject}" has been assigned.',
                                recipient_user_ids=recipients,
                                created_by_user_id=user_id,
                                target_url=f'/tickets/view/{token}/',
                                target_module='tickets',
                                target_record_id=ticket_id
                            )
                except Exception as e:
                    logger.warning(f"Notification error: {str(e)}")
                
                logger.info("Assignment successful")
                return {'success': True}
        except Exception as e:
            logger.error(f"Error assigning ticket: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def update_status(user_id, role_name, ticket_id, new_status, comment=None):
        """Update ticket status with role-based validation"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Ticket_UpdateStatus"(%s::integer, %s::varchar, %s::bigint, %s::varchar, %s::text)
                """, [user_id, role_name, ticket_id, new_status, comment])
                
                result = cursor.fetchone()
                if result and result[0]:
                    return {'success': False, 'error': result[0], 'code': 422}
                
                try:
                    from core.url_encryption import encrypt_id
                    from notifications.services import NotificationService
                    
                    cursor.execute('SELECT "TicketNumber", "Subject", "CreatedByUserID", "AssignedToUserID", "SchoolID" FROM "TicketMaster" WHERE "TicketID" = %s', [ticket_id])
                    ticket_row = cursor.fetchone()
                    if ticket_row:
                        ticket_number, subject, creator_id, assigned_id, school_id = ticket_row
                        token = encrypt_id(ticket_id)
                        
                        recipients = list(set([uid for uid in [creator_id, assigned_id] if uid and uid != user_id]))
                        
                        cursor.execute("""
                            SELECT u."UserID" FROM "UserMaster" u
                            INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                            WHERE p."ProfileName" = 'Super Admin' AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                        """)
                        admin_ids = [row[0] for row in cursor.fetchall()]
                        recipients.extend([aid for aid in admin_ids if aid != user_id and aid not in recipients])
                        
                        if school_id:
                            cursor.execute("""
                                SELECT u."UserID" FROM "UserMaster" u
                                INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                                WHERE p."ProfileName" = 'School Admin' AND u."SchoolID" = %s AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                            """, [school_id])
                            school_admin_ids = [row[0] for row in cursor.fetchall()]
                            recipients.extend([sid for sid in school_admin_ids if sid != user_id and sid not in recipients])
                        
                        if recipients:
                            NotificationService.create_notification(
                                school_id=school_id,
                                type_name='TicketStatusChanged',
                                title=f'Ticket Status Updated: {ticket_number}',
                                message=f'Ticket "{subject}" status changed to {new_status}.',
                                recipient_user_ids=recipients,
                                created_by_user_id=user_id,
                                target_url=f'/tickets/view/{token}/',
                                target_module='tickets',
                                target_record_id=ticket_id
                            )
                except Exception as e:
                    logger.warning(f"Notification error: {str(e)}")
                
                return {'success': True}
        except Exception as e:
            logger.error(f"Error updating ticket status: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def get_ticket_kpis(user_id, role_name, filters=None):
        """Get ticket KPIs (counts by status) without pagination"""
        try:
            filters = filters or {}
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Tickets_GetKPIs"(%s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar, %s::timestamp, %s::timestamp)
                """, [
                    user_id, role_name,
                    filters.get('school_id'),
                    filters.get('assigned_to'),
                    filters.get('status'),
                    filters.get('category'),
                    filters.get('priority'),
                    filters.get('search'),
                    filters.get('from_date'),
                    filters.get('to_date')
                ])
                
                row = cursor.fetchone()
                if row:
                    return {
                        'success': True,
                        'kpis': {
                            'open': row[0] or 0,
                            'in_progress': row[1] or 0,
                            'resolved': row[2] or 0,
                            'closed': row[3] or 0,
                            'reopened': row[4] or 0,
                        }
                    }
                return {'success': True, 'kpis': {'open': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0, 'reopened': 0}}
        except Exception as e:
            logger.error(f"Error getting ticket KPIs: {str(e)}")
            return {'success': False, 'kpis': {'open': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0, 'reopened': 0}}

    @staticmethod
    def get_tickets(user_id, role_name, filters=None, page=1, page_size=10, sort_column='CreatedAt', sort_direction='DESC'):
        """Get tickets based on user role with filtering"""
        try:
            filters = filters or {}
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Tickets_GetByRole"(%s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar, %s::timestamp, %s::timestamp, %s::integer, %s::integer, %s::varchar, %s::varchar)
                """, [
                    user_id, role_name,
                    filters.get('school_id'),
                    filters.get('assigned_to'),
                    filters.get('status'),
                    filters.get('category'),
                    filters.get('priority'),
                    filters.get('search'),
                    filters.get('from_date'),
                    filters.get('to_date'),
                    page, page_size, sort_column, sort_direction
                ])
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                tickets = [dict(zip(columns, row)) for row in rows]
                
                # Log columns for debugging
                logger.info(f"Role {role_name} - Ticket columns: {columns}")
                if tickets:
                    logger.info(f"Role {role_name} - First ticket: {tickets[0]}")
                    # Ensure TicketID exists
                    if 'TicketID' not in tickets[0]:
                        logger.error(f"TicketID missing for role {role_name}")
                
                total_count = tickets[0]['TotalCount'] if tickets else 0
                return {
                    'success': True,
                    'tickets': tickets,
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size
                }
        except Exception as e:
            logger.error(f"Error getting tickets: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def get_ticket_details(user_id, role_name, ticket_id):
        """Get ticket details with activity log (PostgreSQL JSON compatible)"""
        try:
            import json
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Ticket_GetDetails"(%s::integer, %s::varchar, %s::bigint)
                """, [user_id, role_name, ticket_id])
                
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': 'Ticket not found', 'code': 404}
                
                ticket_json, activities_json, comments_json, attachments_json, error_message = row
                
                if error_message:
                    return {'success': False, 'error': error_message, 'code': 403}
                
                # Parse JSON data
                ticket = json.loads(ticket_json) if ticket_json else None
                activities = json.loads(activities_json) if activities_json else []
                comments = json.loads(comments_json) if comments_json else []
                attachments = json.loads(attachments_json) if attachments_json else []
                
                if not ticket:
                    return {'success': False, 'error': 'Ticket not found', 'code': 404}
                
                return {
                    'success': True,
                    'ticket': ticket,
                    'activities': activities,
                    'comments': comments,
                    'attachments': attachments
                }
        except Exception as e:
            logger.error(f"Error getting ticket details: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def add_comment(ticket_id, user_id, comment_text, is_internal=False, file_data=None, file_name=None, file_size=None, content_type=None, reply_to_comment_id=None):
        """Add a comment to a ticket with optional attachment and reply"""
        try:
            with connection.cursor() as cursor:
                # Insert attachment first if provided
                attachment_id = None
                if file_data:
                    cursor.execute("""
                        INSERT INTO "TicketAttachments" ("TicketID", "FileName", "FilePath", "FileData", "FileSize", "ContentType", "UploadedByUserID", "UploadedAt", "IsDeleted")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, FALSE)
                        RETURNING "AttachmentID"
                    """, [ticket_id, file_name, '', file_data, file_size, content_type, user_id])
                    result = cursor.fetchone()
                    if result:
                        attachment_id = result[0]
                
                # Insert comment and get ID
                cursor.execute("""
                    INSERT INTO "TicketComments" ("TicketID", "CommentByUserID", "CommentText", "IsInternal", "AttachmentID", "ReplyToCommentID", "CreatedAt", "IsDeleted")
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, FALSE)
                    RETURNING "CommentID";
                """, [ticket_id, user_id, comment_text, is_internal, attachment_id, reply_to_comment_id])
                
                result = cursor.fetchone()
                comment_id = result[0] if result else None
                
                # Update ticket timestamp
                cursor.execute('UPDATE "TicketMaster" SET "UpdatedAt" = CURRENT_TIMESTAMP WHERE "TicketID" = %s', [ticket_id])
                
                try:
                    from notifications.services import NotificationService
                    from core.url_encryption import encrypt_id
                    
                    cursor.execute('''
                        SELECT t."TicketNumber", t."CreatedByUserID", t."AssignedToUserID", t."SchoolID"
                        FROM "TicketMaster" t WHERE t."TicketID" = %s
                    ''', [ticket_id])
                    ticket_row = cursor.fetchone()
                    
                    if ticket_row:
                        ticket_number, creator_id, assigned_id, school_id = ticket_row
                        recipients = list(set([uid for uid in [creator_id, assigned_id] if uid and uid != user_id]))
                        
                        cursor.execute("""
                            SELECT u."UserID" FROM "UserMaster" u
                            INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                            WHERE p."ProfileName" = 'Super Admin' AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                        """)
                        admin_ids = [row[0] for row in cursor.fetchall()]
                        recipients.extend([aid for aid in admin_ids if aid != user_id and aid not in recipients])
                        
                        if school_id:
                            cursor.execute("""
                                SELECT u."UserID" FROM "UserMaster" u
                                INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                                WHERE p."ProfileName" = 'School Admin' AND u."SchoolID" = %s AND u."IsActive" = TRUE AND COALESCE(u."IsDeleted", FALSE) = FALSE
                            """, [school_id])
                            school_admin_ids = [row[0] for row in cursor.fetchall()]
                            recipients.extend([sid for sid in school_admin_ids if sid != user_id and sid not in recipients])
                        
                        if recipients:
                            token = encrypt_id(ticket_id)
                            NotificationService.create_notification(
                                school_id=school_id,
                                type_name='TicketChatMessage',
                                title=f'New message on {ticket_number}',
                                message=comment_text[:100] + '...' if len(comment_text) > 100 else comment_text,
                                recipient_user_ids=recipients,
                                created_by_user_id=user_id,
                                target_url=f'/tickets/view/{token}/#chat',
                                target_module='tickets',
                                target_record_id=ticket_id
                            )
                except Exception as e:
                    logger.warning(f"Notification error: {str(e)}")
                
                return {'success': True, 'comment_id': comment_id, 'attachment_id': attachment_id}
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def get_support_executives(school_id=None):
        """Get list of support executives for assignment"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM "Proc_Support_Executive_dropdown_list_get"()')
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                executives = [dict(zip(columns, row)) for row in rows]
                
                logger.info(f"Support executives loaded: {executives}")
                
                return {'success': True, 'executives': executives}
        except Exception as e:
            logger.error(f"Error getting support executives: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}

    @staticmethod
    def get_ticket_insights(user_id, role_name, start_date=None, end_date=None, school_id=None):
        """Get ticket insights dashboard data"""
        try:
            import json
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Ticket_Insights_Dashboard"(%s::integer, %s::varchar, %s::timestamp, %s::timestamp, %s::integer)
                """, [user_id, role_name, start_date, end_date, school_id])
                
                row = cursor.fetchone()
                if row:
                    stats = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
                    trends = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or [])
                    categories = json.loads(row[2]) if isinstance(row[2], str) else (row[2] or [])
                    priorities = json.loads(row[3]) if isinstance(row[3], str) else (row[3] or [])
                    performers = json.loads(row[4]) if isinstance(row[4], str) else (row[4] or [])
                    schools = json.loads(row[5]) if isinstance(row[5], str) else (row[5] or [])
                    
                    return {
                        'success': True,
                        'stats': stats,
                        'trends': trends,
                        'categories': categories,
                        'priorities': priorities,
                        'performers': performers,
                        'schools': schools
                    }
                else:
                    return {'success': False, 'error': 'No data returned', 'code': 500}
        except Exception as e:
            logger.error(f"Error getting ticket insights: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e), 'code': 500}
