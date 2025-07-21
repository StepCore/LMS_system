from django.core.management.base import BaseCommand
from users.models import Payment, User
from materials.models import Course, Lesson


class Command(BaseCommand):
    help = 'Загрузка тестовых платежей в базу данных'

    def handle(self, *args, **options):
        try:
            # Создаем тестовых пользователей, если их нет
            user1, _ = User.objects.get_or_create(
                email='user1@example.com',
                defaults={
                    'phone': '+79991112233',
                    'city': 'Москва'
                }
            )

            user2, _ = User.objects.get_or_create(
                email='user2@example.com',
                defaults={
                    'phone': '+79994445566',
                    'city': 'Санкт-Петербург'
                }
            )

            # Создаем тестовые курсы и уроки, если их нет
            course1, _ = Course.objects.get_or_create(
                name='Python Basics',
                defaults={
                    'description': 'Базовый курс по Python'
                }
            )

            course2, _ = Course.objects.get_or_create(
                name='Django Pro',
                defaults={
                    'description': 'Продвинутый курс по Django'
                }
            )

            lesson1, _ = Lesson.objects.get_or_create(
                name='Введение в Python',
                defaults={
                    'course': course1,
                    'description': 'Основы языка Python'
                }
            )

            lesson2, _ = Lesson.objects.get_or_create(
                name='Модели Django',
                defaults={
                    'course': course2,
                    'description': 'Работа с моделями в Django'
                }
            )

            payments_data = [
                {
                    'user': user1,
                    'paid_course': course1,
                    'paid_lesson': None,
                    'amount': 5000.00,
                    'payment_method': 'transfer'
                },
                {
                    'user': user1,
                    'paid_course': None,
                    'paid_lesson': lesson1,
                    'amount': 1500.00,
                    'payment_method': 'cash'
                },
                {
                    'user': user2,
                    'paid_course': course2,
                    'paid_lesson': None,
                    'amount': 7500.00,
                    'payment_method': 'transfer'
                }
            ]

            for payment_data in payments_data:
                Payment.objects.create(**payment_data)

            self.stdout.write(self.style.SUCCESS('Успешно загружены тестовые платежи'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))
