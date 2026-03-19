from celery import current_app
from django.conf import settings


class PriorityQueueManager:
    """Gestor de colas de prioridad para Celery."""

    PRIORITY_LEVELS = {
        "critical": 10,
        "high": 9,
        "normal": 5,
        "low": 1,
    }

    QUEUE_MAPPING = {
        "critical": "high_priority",
        "high": "high_priority",
        "normal": "normal_priority",
        "low": "low_priority",
    }

    @classmethod
    def send_task_with_priority(
        cls, task_name, args=None, kwargs=None, priority="normal"
    ):
        """Enviar tarea con prioridad específica."""
        queue = cls.QUEUE_MAPPING.get(priority, "normal_priority")
        priority_level = cls.PRIORITY_LEVELS.get(priority, 5)

        return current_app.send_task(
            task_name,
            args=args or [],
            kwargs=kwargs or {},
            queue=queue,
            priority=priority_level,
        )

    @classmethod
    def get_queue_status(cls):
        """Obtener estado de las colas."""
        inspect = current_app.control.inspect()

        stats = {
            "active": inspect.active() or {},
            "scheduled": inspect.scheduled() or {},
            "reserved": inspect.reserved() or {},
        }

        return stats

    @classmethod
    def purge_queue(cls, queue_name):
        """Limpiar cola específica."""
        return current_app.control.purge(queue_name)

    @classmethod
    def get_queue_length(cls, queue_name):
        """Obtener longitud de cola específica."""
        with current_app.broker_connection() as conn:
            return conn.default_channel.client.llen(f"celery:{queue_name}")


def send_priority_email(subject, message, recipients, priority="high"):
    """Helper para enviar emails con prioridad."""
    from core.tasks import send_notification_email

    return PriorityQueueManager.send_task_with_priority(
        "core.tasks.send_notification_email",
        args=[subject, message, recipients],
        priority=priority,
    )


def schedule_data_processing(data_id, priority="normal"):
    """Helper para programar procesamiento de datos."""
    from core.tasks import process_location_data

    return PriorityQueueManager.send_task_with_priority(
        "core.tasks.process_location_data", priority=priority
    )


def schedule_maintenance_task(task_type="cleanup", priority="low"):
    """Helper para programar tareas de mantenimiento."""
    task_mapping = {
        "cleanup": "core.tasks.cleanup_old_data",
        "backup": "core.tasks.backup_data",
    }

    task_name = task_mapping.get(task_type)
    if not task_name:
        raise ValueError(f"Unknown maintenance task: {task_type}")

    return PriorityQueueManager.send_task_with_priority(task_name, priority=priority)
