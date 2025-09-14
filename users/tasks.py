from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


@shared_task
def check_and_block_inactive_users():
    """Проверяет пользователей, которые не заходили более месяца, и блокирует их"""
    one_month_ago = timezone.now() - timedelta(days=30)

    inactive_users = User.objects.filter(is_active=True, last_login__lt=one_month_ago)

    blocked_count = 0
    for user in inactive_users:
        user.is_active = False
        user.save()
        blocked_count += 1

        # Отправляем уведомление о блокировке
        send_mail(
            subject="Ваш аккаунт был заблокирован",
            message=f"Уважаемый {user.email}, ваш аккаунт был заблокирован "
            f"из-за неактивности (последний вход: {user.last_login}).",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    print(f"Заблокировано {blocked_count} неактивных пользователей")
    return f"Blocked {blocked_count} inactive users"


@shared_task
def send_inactivity_warning():
    """Отправка предупреждения пользователям, которые не заходили 3 недели"""
    three_weeks_ago = timezone.now() - timedelta(days=21)

    users_to_warn = User.objects.filter(
        is_active=True,
        last_login__lt=three_weeks_ago,
        last_login__gt=timezone.now() - timedelta(days=28),
    )

    for user in users_to_warn:
        send_mail(
            subject="Предупреждение о неактивности аккаунта",
            message=f"Уважаемый {user.email}, вы не заходили в систему более 3 недель. "
            f"Через неделю ваш аккаунт будет заблокирован.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    return f"Sent warnings to {users_to_warn.count()} users"
