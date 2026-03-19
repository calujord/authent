from celery import current_app
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.tasks import (
    backup_data,
    cleanup_old_data,
    generate_reports,
    process_location_data,
    process_urgent_data,
    send_notification_email,
)


class Command(BaseCommand):
    help = "Monitor Celery queue status and priorities"

    def add_arguments(self, parser):
        parser.add_argument(
            "--inspect",
            action="store_true",
            help="Inspect active tasks and queue status",
        )
        parser.add_argument(
            "--test-tasks",
            action="store_true",
            help="Send test tasks to different priority queues",
        )

    def handle(self, *args, **options):
        if options["inspect"]:
            self.inspect_queues()

        if options["test_tasks"]:
            self.test_priority_tasks()

    def inspect_queues(self):
        """Inspect current queue status."""
        self.stdout.write(self.style.SUCCESS("=== Queue Status ==="))

        # Inspect active tasks
        inspect = current_app.control.inspect()

        self.stdout.write("Active tasks:")
        active = inspect.active()
        if active:
            for worker, tasks in active.items():
                self.stdout.write(f"Worker: {worker}")
                for task in tasks:
                    self.stdout.write(f"  - {task['name']} (ID: {task['id'][:8]}...)")
        else:
            self.stdout.write("  No active tasks")

        self.stdout.write("\nScheduled tasks:")
        scheduled = inspect.scheduled()
        if scheduled:
            for worker, tasks in scheduled.items():
                self.stdout.write(f"Worker: {worker}")
                for task in tasks:
                    self.stdout.write(f"  - {task['request']['task']} at {task['eta']}")
        else:
            self.stdout.write("  No scheduled tasks")

        # Reserved tasks
        self.stdout.write("\nReserved tasks:")
        reserved = inspect.reserved()
        if reserved:
            for worker, tasks in reserved.items():
                self.stdout.write(f"Worker: {worker}: {len(tasks)} tasks")
        else:
            self.stdout.write("  No reserved tasks")

    def test_priority_tasks(self):
        """Send test tasks to different priority queues."""
        self.stdout.write(self.style.SUCCESS("=== Sending Test Tasks ==="))

        # High priority tasks
        self.stdout.write("Sending HIGH priority tasks...")
        result1 = send_notification_email.delay(
            "Test High Priority",
            "This is a high priority email test",
            ["test@example.com"],
        )
        self.stdout.write(f"  Email task: {result1.id}")

        result2 = process_urgent_data.delay("urgent_data_123")
        self.stdout.write(f"  Urgent data task: {result2.id}")

        # Normal priority tasks
        self.stdout.write("Sending NORMAL priority tasks...")
        result3 = process_location_data.delay()
        self.stdout.write(f"  Location data task: {result3.id}")

        result4 = generate_reports.delay("monthly_report")
        self.stdout.write(f"  Report generation task: {result4.id}")

        # Low priority tasks
        self.stdout.write("Sending LOW priority tasks...")
        result5 = cleanup_old_data.delay()
        self.stdout.write(f"  Cleanup task: {result5.id}")

        result6 = backup_data.delay("incremental")
        self.stdout.write(f"  Backup task: {result6.id}")

        self.stdout.write(
            self.style.SUCCESS(
                "All test tasks sent! Use --inspect to monitor progress."
            )
        )
