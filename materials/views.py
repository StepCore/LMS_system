from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.generics import (CreateAPIView, DestroyAPIView,
                                     ListAPIView, RetrieveAPIView,
                                     UpdateAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from materials import tasks
from materials.models import Course, Lesson
from materials.paginators import CoursePagination, LessonPagination
from materials.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModer, IsOwner


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.prefetch_related("lesson").all()
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "destroy"]:
            permission_classes = [IsOwner]
        else:
            permission_classes = []

        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        """Передаем request в контекст сериализатора"""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def update(self, request, *args, **kwargs):
        """Обновление курса с отправкой уведомлений подписчикам"""
        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            course = self.get_object()

            # Формируем сообщение об обновлении
            update_message = f"Курс '{course.name}' был обновлен. "
            if "description" in request.data:
                update_message += "Изменено описание курса."
            elif "name" in request.data:
                update_message += "Изменено название курса."
            else:
                update_message += "Внесены изменения в материалы курса."

            # Асинхронная отправка уведомлений подписчикам
            tasks.send_course_update_notification.delay(course.id, update_message)

        return response

    @action(detail=True, methods=["post"])
    def add_lesson(self, request):
        """Добавление урока к курсу с уведомлением подписчиков"""
        course = self.get_object()

        # Уведомление подписчиков
        lesson_name = request.data.get("name", "новый урок")
        update_message = f"Добавлен новый урок: {lesson_name}"
        tasks.send_course_update_notification.delay(course.id, update_message)

        return Response({"message": "Lesson added and notifications sent"})


class LessonCreateApiView(CreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def perform_create(self, serializer):
        permission_classes = [~IsModer, IsAuthenticated]
        lesson = serializer.save()
        lesson.owner = self.request.user
        lesson.save()

        return [permission() for permission in permission_classes]


class LessonListApiView(ListAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = LessonPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ("course",)
    permission_classes = [permissions.AllowAny]


class LessonRetrieveApiView(RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]


class LessonUpdateApiView(UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModer | IsOwner]


class LessonDestroyApiView(DestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwner | ~IsModer]
