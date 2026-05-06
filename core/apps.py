from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Start the email worker when Django starts"""
        try:
            from .database_email_queue import database_email_queue
            
            # Start the email worker if not already running
            if not database_email_queue.processing:
                database_email_queue.start_worker()
                logger.info("Email worker started successfully")
            else:
                logger.info("Email worker already running")
                
        except Exception as e:
            logger.error(f"Failed to start email worker: {str(e)}")
            # Don't raise the exception to avoid breaking Django startup
