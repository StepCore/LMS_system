from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Расписание периодических задач
app.conf.beat_schedule = {
    # Блокировка неактивных пользователей - каждый день в 2:00
    "block-inactive-users-daily": {
        "task": "users.tasks.check_and_block_inactive_users",
        "schedule": crontab(hour=2, minute=0),
    },
    # Предупреждение о неактивности - каждый понедельник в 10:00
    "send-inactivity-warnings-weekly": {
        "task": "users.tasks.send_inactivity_warning",
        "schedule": crontab(hour=10, minute=0, day_of_week=1),
    },
    # Еженедельная рассылка обновлений курсов - каждый понедельник в 9:00
    "send-weekly-course-updates": {
        "task": "materials.tasks.send_course_updates",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
    # Очистка старых платежей - первое число каждого месяца в 3:00
    "cleanup-old-payments-monthly": {
        "task": "users.tasks.cleanup_old_payments",
        "schedule": crontab(hour=3, minute=0, day_of_month=1),
    },
}
