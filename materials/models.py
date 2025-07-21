from django.db import models


class Course(models.Model):

    name = models.CharField(
        max_length=35,
        unique=True,
        verbose_name="Название курса",
        help_text="Укажите название курса",
    )
    photo = models.ImageField(
        upload_to="users/course",
        blank=True,
        null=True,
        verbose_name="Изображение",
        help_text="Загрузите изображение курса",
    )
    description = models.CharField(
        verbose_name="Описание курса",
        help_text="Укажите описание курса",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"


class Lesson(models.Model):

    name = models.CharField(
        max_length=35,
        unique=True,
        verbose_name="Название урока",
        help_text="Укажите название урока",
    )
    photo = models.ImageField(
        upload_to="users/course",
        blank=True,
        null=True,
        verbose_name="Изображение",
        help_text="Загрузите изображение урока",
    )
    description = models.CharField(
        verbose_name="Описание урока",
        help_text="Укажите описание урока",
        blank=True,
        null=True,
    )

    video_url = models.URLField(
        verbose_name="Ссылка на видео",
        help_text="Введите URL-адрес видео",
        blank=True,
        null=True,
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lesson',
        verbose_name="Курс",
        help_text="Выберите курс",
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
