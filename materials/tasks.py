from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from users.models import Subscription
from .models import Course


@shared_task
def send_course_update_notification(course_id, update_message):
    """Асинхронная отправка уведомлений об обновлении курса подписанным пользователям"""
    try:
        course = Course.objects.get(id=course_id)
        subscribers = Subscription.objects.filter(course=course).select_related("user")

        if not subscribers.exists():
            return f"No subscribers for course {course.name}"

        subject = f"Обновление курса: {course.name}"

        for subscription in subscribers:
            user = subscription.user

            # Формируем HTML письмо
            html_message = render_to_string(
                "emails/course_update.html",
                {
                    "user": user,
                    "course": course,
                    "update_message": update_message,
                },
            )

            plain_message = strip_tags(html_message)

            # Отправляем email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"Отправлено уведомление для {user.email} о курсе {course.name}")

        return f"Sent updates to {subscribers.count()} subscribers for course {course.name}"

    except Course.DoesNotExist:
        return f"Course with id {course_id} not found"
    except Exception as e:
        return f"Error sending notifications: {str(e)}"
