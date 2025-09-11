from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None

    email = models.EmailField(
        unique=True, verbose_name="Почта", help_text="Укажите почту"
    )
    phone = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name="Номер телефон",
        help_text="Укажите номер телефона",
    )
    avatar = models.ImageField(
        upload_to="users/avatars",
        blank=True,
        null=True,
        verbose_name="Аватар",
        help_text="Загрузите фото профиля",
    )
    city = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name="Город",
        help_text="Укажите город",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Meta:
    verbose_name = "Пользователь"
    verbose_name_plural = "Пользователи"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("cash", "Наличные"),
        ("transfer", "Перевод на счет"),
        ("stripe", "Stripe"),
    ]

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Пользователь",
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплаты")
    paid_course = models.ForeignKey(
        "materials.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный курс",
    )
    paid_lesson = models.ForeignKey(
        "materials.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный урок",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Сумма оплаты"
    )
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, verbose_name="Способ оплаты"
    )

    # Новые поля для Stripe
    stripe_product_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID продукта в Stripe"
    )
    stripe_price_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID цены в Stripe"
    )
    stripe_session_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID сессии в Stripe"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID платежа в Stripe"
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"Платеж {self.amount} от {self.user.email}"


class Subscription(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Пользователь",
    )
    course = models.ForeignKey(
        "materials.Course",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Курс",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ["user", "course"]

    def __str__(self):
        return f"{self.user.email} - {self.course.name}"
