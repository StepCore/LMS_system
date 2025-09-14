from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Course, Lesson

User = get_user_model()


class LessonCRUDTestCase(APITestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем пользователей
        self.admin_user = User.objects.create(
            email="admin@test.com", password="testpass123", is_staff=True
        )
        self.regular_user = User.objects.create(
            email="user@test.com", password="testpass123"
        )
        self.other_user = User.objects.create(
            email="other@test.com", password="testpass123"
        )

        # Создаем курсы
        self.course1 = Course.objects.create(
            name="Test Course 1",
            description="Test Description 1",
            owner=self.admin_user,
        )
        self.course2 = Course.objects.create(
            name="Test Course 2",
            description="Test Description 2",
            owner=self.regular_user,
        )

        # Создаем уроки
        self.lesson1 = Lesson.objects.create(
            name="Test Lesson 1",
            description="Test Lesson Description 1",
            course=self.course1,
            owner=self.admin_user,
            video_url="https://www.youtube.com/watch?v=test1",
        )
        self.lesson2 = Lesson.objects.create(
            name="Test Lesson 2",
            description="Test Lesson Description 2",
            course=self.course2,
            owner=self.regular_user,
            video_url="https://www.youtube.com/watch?v=test2",
        )

        # URL для тестов
        self.lessons_list_url = reverse("materials:lessons_list")
        self.lesson_detail_url = reverse(
            "materials:lessons_retrieve", kwargs={"pk": self.lesson1.pk}
        )
        self.lesson_create_url = reverse("materials:lessons_create")
        self.lesson_update_url = reverse(
            "materials:lessons_update", kwargs={"pk": self.lesson1.pk}
        )
        self.lesson_delete_url = reverse(
            "materials:lessons_delete", kwargs={"pk": self.lesson1.pk}
        )

    def test_get_lessons_list_authenticated(self):
        """Тест получения списка уроков аутентифицированным пользователем"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.lessons_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # С пагинацией

    def test_get_lessons_list_unauthenticated(self):
        """Тест получения списка уроков неаутентифицированным пользователем"""
        response = self.client.get(self.lessons_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_lesson_detail_authenticated(self):
        """Тест получения деталей урока аутентифицированным пользователем"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.lesson_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Lesson 1")

    def test_create_lesson_authenticated(self):
        """Тест создания урока аутентифицированным пользователем"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            "name": "New Test Lesson",
            "description": "New Test Description",
            "course": self.course2.pk,
            "video_url": "https://www.youtube.com/watch?v=newtest",
        }
        response = self.client.post(self.lesson_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 3)

    def test_create_lesson_unauthenticated(self):
        """Тест создания урока неаутентифицированным пользователем"""
        data = {
            "name": "New Test Lesson",
            "description": "New Test Description",
            "course": self.course2.pk,
            "video_url": "https://www.youtube.com/watch?v=newtest",
        }
        response = self.client.post(self.lesson_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_lesson_with_invalid_video_url(self):
        """Тест создания урока с невалидной ссылкой на видео"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            "name": "New Test Lesson",
            "description": "New Test Description",
            "course": self.course2.pk,
            "video_url": "https://vimeo.com/test",  # Не YouTube
        }
        response = self.client.post(self.lesson_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_lesson_owner(self):
        """Тест обновления урока владельцем"""
        lesson_owned = Lesson.objects.create(
            name="Owned Lesson",
            description="Owned Description",
            course=self.course2,  # Курс принадлежит regular_user
            owner=self.regular_user,
            video_url="https://www.youtube.com/watch?v=owned",
        )

        update_url = reverse("materials:lessons_update", kwargs={"pk": lesson_owned.pk})
        self.client.force_authenticate(user=self.regular_user)
        data = {"name": "Updated Lesson Name"}
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lesson_owned.refresh_from_db()
        self.assertEqual(lesson_owned.name, "Updated Lesson Name")

    def test_update_lesson_not_owner(self):
        """Тест обновления урока не владельцем"""
        self.client.force_authenticate(user=self.other_user)
        data = {"name": "Updated Lesson Name"}
        response = self.client.patch(self.lesson_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_lesson_owner(self):
        """Тест удаления урока владельцем"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.lesson_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_delete_lesson_not_owner(self):
        """Тест удаления урока не владельцем"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.lesson_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 2)
