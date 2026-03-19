from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail

logger = get_task_logger(__name__)


@shared_task(bind=True, priority=9)
def send_notification_email(self, subject, message, recipient_list):
    """High priority task for sending notification emails."""
    try:
        logger.info(f"Sending high priority email: {subject}")
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Email sent to {len(recipient_list)} recipients"
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, priority=9)
def process_urgent_data(self, data_id):
    """High priority task for processing urgent data."""
    try:
        logger.info(f"Processing urgent data: {data_id}")
        # Simulate urgent processing
        import time

        time.sleep(2)
        return f"Urgent data {data_id} processed successfully"
    except Exception as e:
        logger.error(f"Error processing urgent data: {str(e)}")
        raise self.retry(countdown=30, max_retries=5)


@shared_task(bind=True, priority=5)
def process_location_data(self):
    """Normal priority task for processing location data."""
    try:
        from .models import Location

        logger.info("Processing location data")
        locations_count = Location.objects.filter(is_active=True).count()
        return f"Processed {locations_count} active locations"
    except Exception as e:
        logger.error(f"Error processing locations: {str(e)}")
        raise self.retry(countdown=120, max_retries=3)


@shared_task(bind=True, priority=5)
def generate_reports(self, report_type):
    """Normal priority task for generating reports."""
    try:
        logger.info(f"Generating report: {report_type}")
        # Simulate report generation
        import time

        time.sleep(10)
        return f"Report {report_type} generated successfully"
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise self.retry(countdown=300, max_retries=2)


@shared_task(bind=True, priority=1)
def cleanup_old_data(self):
    """Low priority task for cleaning old data."""
    try:
        from datetime import timedelta

        from django.utils import timezone

        from .models import Location

        logger.info("Starting old data cleanup")
        cutoff_date = timezone.now() - timedelta(days=365)
        deleted_count, _ = Location.objects.filter(
            created_at__lt=cutoff_date, is_active=False
        ).delete()

        return f"Deleted {deleted_count} old locations"
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        raise self.retry(countdown=600, max_retries=2)


@shared_task(bind=True, priority=1)
def backup_data(self, backup_type="full"):
    """Low priority task for backups."""
    try:
        logger.info(f"Starting backup: {backup_type}")
        # Simulate backup
        import time

        time.sleep(30)
        return f"Backup {backup_type} completed successfully"
    except Exception as e:
        logger.error(f"Error in backup: {str(e)}")
        raise self.retry(countdown=3600, max_retries=1)


@shared_task(bind=True, priority=1, ignore_result=True)
def cleanup_celery_beat_schedules(self):
    """
    Remove orphaned schedule entries not referenced by any PeriodicTask.
    Runs monthly as a safety net to prevent schedule table bloat.
    """
    from django_celery_beat.models import (
        ClockedSchedule,
        CrontabSchedule,
        IntervalSchedule,
        SolarSchedule,
    )

    total_deleted = 0

    for Model in [IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule]:
        deleted, _ = Model.objects.filter(periodictask=None).delete()
        if deleted:
            logger.info(f"Cleaned {deleted} orphaned {Model.__name__} entries")
            total_deleted += deleted

    logger.info(
        f"Celery beat schedule cleanup completed: {total_deleted} orphaned entries removed"
    )
    return f"{total_deleted} orphaned entries removed"


@shared_task(bind=True)
def process_bulk_data(self, data_batch, priority_level=5):
    """Configurable task for bulk processing."""
    try:
        # Change priority dynamically
        self.update_state(
            state="PROGRESS", meta={"current": 0, "total": len(data_batch)}
        )

        processed = 0
        for item in data_batch:
            # Process item
            processed += 1
            self.update_state(
                state="PROGRESS", meta={"current": processed, "total": len(data_batch)}
            )

        return f"Processed {processed} elements successfully"
    except Exception as e:
        logger.error(f"Error in bulk processing: {str(e)}")
        raise self.retry(countdown=180, max_retries=3)


# =============================================================================
# Push Notification Tasks
# =============================================================================


@shared_task(bind=True, priority=9)
def send_push_notification(
    self,
    user_id: int,
    title: str,
    body: str,
    data: dict = None,
    click_action: str = None,
):
    """
    High priority task for sending push notification to a user.

    Args:
        user_id: Target user ID
        title: Notification title
        body: Notification body text
        data: Optional data payload
        click_action: URL/deep link to open on click
    """
    try:
        from core.services.notifications import NotificationService

        logger.info(f"Sending push notification to user {user_id}: {title}")

        results = NotificationService.send_to_user(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            click_action=click_action,
        )

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        logger.info(
            f"Push notification sent to user {user_id}: "
            f"{success_count} success, {failure_count} failed"
        )

        return {
            "user_id": user_id,
            "success_count": success_count,
            "failure_count": failure_count,
        }

    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, priority=8)
def send_push_notification_bulk(
    self,
    user_ids: list,
    title: str,
    body: str,
    data: dict = None,
    click_action: str = None,
):
    """
    Send push notification to multiple users.

    Args:
        user_ids: List of target user IDs
        title: Notification title
        body: Notification body text
        data: Optional data payload
        click_action: URL/deep link to open on click
    """
    try:
        from core.services.notifications import NotificationService

        logger.info(f"Sending bulk push notification to {len(user_ids)} users")

        results = NotificationService.send_to_users(
            user_ids=user_ids,
            title=title,
            body=body,
            data=data,
            click_action=click_action,
        )

        total_success = 0
        total_failure = 0
        for user_results in results.values():
            total_success += sum(1 for r in user_results if r.success)
            total_failure += sum(1 for r in user_results if not r.success)

        logger.info(
            f"Bulk push notification complete: "
            f"{total_success} success, {total_failure} failed"
        )

        return {
            "users_count": len(user_ids),
            "success_count": total_success,
            "failure_count": total_failure,
        }

    except Exception as e:
        logger.error(f"Error in bulk push notification: {str(e)}")
        raise self.retry(countdown=120, max_retries=2)


@shared_task(bind=True, priority=7)
def send_push_notification_topic(
    self,
    topic: str,
    title: str,
    body: str,
    data: dict = None,
):
    """
    Send push notification to a topic (all subscribed devices).

    Args:
        topic: Topic name (e.g., "promotions", "news")
        title: Notification title
        body: Notification body text
        data: Optional data payload
    """
    try:
        from core.services.notifications import NotificationService

        logger.info(f"Sending topic notification to '{topic}': {title}")

        result = NotificationService.send_to_topic(
            topic=topic,
            title=title,
            body=body,
            data=data,
        )

        if result.success:
            logger.info(f"Topic notification sent: {result.message_id}")
            return {
                "topic": topic,
                "success": True,
                "message_id": result.message_id,
            }
        else:
            logger.error(f"Topic notification failed: {result.error}")
            return {
                "topic": topic,
                "success": False,
                "error": result.error,
            }

    except Exception as e:
        logger.error(f"Error in topic notification: {str(e)}")
        raise self.retry(countdown=120, max_retries=2)
