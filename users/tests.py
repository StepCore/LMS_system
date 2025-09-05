from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from materials.models import Course
from users.models import Subscription

User = get_user_model()


class SubscriptionTestCase(APITestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем пользователей
        self.user1 = User.objects.create(
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create(
            email='user2@test.com',
            password='testpass123'
        )

        # Создаем курсы
        self.course1 = Course.objects.create(
            name='Test Course 1',
            description='Test Description 1',
            owner=self.user1
        )
        self.course2 = Course.objects.create(
            name='Test Course 2',
            description='Test Description 2',
            owner=self.user2
        )

        # URL для тестов
        self.subscription_url = reverse('users:subscription')

    def test_create_subscription(self):
        """Тест создания подписки"""
        self.client.force_authenticate(user=self.user1)
        data = {'course_id': self.course1.pk}

        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка добавлена')
        self.assertTrue(Subscription.objects.filter(user=self.user1, course=self.course1).exists())

    def test_delete_subscription(self):
        """Тест удаления подписки"""
        # Сначала создаем подписку
        Subscription.objects.create(user=self.user1, course=self.course1)

        self.client.force_authenticate(user=self.user1)
        data = {'course_id': self.course1.pk}

        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка удалена')
        self.assertFalse(Subscription.objects.filter(user=self.user1, course=self.course1).exists())

    def test_subscription_unauthenticated(self):
        """Тест подписки неаутентифицированным пользователем"""
        data = {'course_id': self.course1.pk}
        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscription_invalid_course(self):
        """Тест подписки на несуществующий курс"""
        self.client.force_authenticate(user=self.user1)
        data = {'course_id': 999}  # Несуществующий ID

        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_missing_course_id(self):
        """Тест подписки без указания course_id"""
        self.client.force_authenticate(user=self.user1)
        data = {}  # Отсутствует course_id

        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscription_is_included_in_course_response(self):
        """Тест, что информация о подписке включается в ответ курса"""
        # Создаем подписку
        Subscription.objects.create(user=self.user1, course=self.course1)

        self.client.force_authenticate(user=self.user1)
        course_url = reverse('materials:course-detail', kwargs={'pk': self.course1.pk})

        response = self.client.get(course_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])

    def test_subscription_not_included_for_other_user(self):
        """Тест, что подписка одного пользователя не влияет на другого"""
        # User1 подписан на курс
        Subscription.objects.create(user=self.user1, course=self.course1)

        # User2 запрашивает курс
        self.client.force_authenticate(user=self.user2)
        course_url = reverse('materials:course-detail', kwargs={'pk': self.course1.pk})

        response = self.client.get(course_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_subscribed'])