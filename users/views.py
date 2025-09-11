import secrets

import stripe
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from config.settings import EMAIL_HOST_USER, STRIPE_SECRET_KEY
from materials.models import Course

from .filters import PaymentFilter
from .forms import UserRegisterForm
from .models import Payment, Subscription, User
from .permissions import IsOwner
from .serializers import (PaymentCancelSerializer, PaymentSerializer,
                          PaymentSessionSerializer, PaymentSuccessSerializer,
                          UserSerializer)
from .services import StripeService


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Возвращаем все платежи или только для авторизованного пользователя"""
        queryset = Payment.objects.select_related("user", "paid_course", "paid_lesson")

        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()

    def get_permissions(self):
        if self.action in ["update", "destroy"]:
            permission_classes = [IsOwner]
        elif self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"
        send_mail(
            subject="Подтверждение почты",
            message=f"Для подтверждения почты необходимо перейти по ссылке, чтобы завершить регистрацию {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


def email_verification(token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse("users:login"))


class SubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        course_id = request.data.get("course_id")

        if not course_id:
            return Response(
                {"error": "course_id обязателен"}, status=status.HTTP_400_BAD_REQUEST
            )

        course_item = get_object_or_404(Course, id=course_id)
        subs_item = Subscription.objects.filter(user=user, course=course_item)

        if subs_item.exists():
            subs_item.delete()
            message = "Подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = "Подписка добавлена"

        return Response({"message": message}, status=status.HTTP_200_OK)


stripe.api_key = STRIPE_SECRET_KEY


class CreatePaymentSessionAPIView(APIView):
    """Создание сессии оплаты для курса через Stripe. Возвращает URL для перенаправления на страницу оплаты."""

    @swagger_auto_schema(
        operation_description="Создает сессию оплаты для указанного курса",
        responses={
            200: PaymentSessionSerializer(),
            404: "Курс не найден",
            400: "Ошибка Stripe",
        },
        manual_parameters=[
            openapi.Parameter(
                "course_id",
                openapi.IN_PATH,
                description="ID курса для оплаты",
                type=openapi.TYPE_INTEGER,
            )
        ],
    )
    def post(self, request, course_id):
        user = request.user
        course = get_object_or_404(Course, id=course_id)

        try:
            product = StripeService.create_product(
                name=course.name, description=course.description or "Оплата курса"
            )

            price = StripeService.create_price(
                product_id=product.id, amount=10000  # Указываем цену за курс
            )

            success_url = request.build_absolute_uri(
                reverse("payment-success") + f"?session_id={{CHECKOUT_SESSION_ID}}"
            )
            cancel_url = request.build_absolute_uri(reverse("payment-cancel"))

            session = StripeService.create_checkout_session(
                price_id=price.id, success_url=success_url, cancel_url=cancel_url
            )

            payment = Payment.objects.create(
                user=user,
                paid_course=course,
                amount=100,
                payment_method="stripe",
                stripe_product_id=product.id,
                stripe_price_id=price.id,
                stripe_session_id=session.id,
            )

            serializer = PaymentSessionSerializer(
                {
                    "session_id": session.id,
                    "payment_url": session.url,
                    "payment_id": payment.id,
                }
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentSuccessAPIView(APIView):
    """Эндпоинт для обработки успешной оплаты. Stripe перенаправляет сюда после успешного платежа."""

    @swagger_auto_schema(
        operation_description="Обработка успешной оплаты (редирект от Stripe)",
        responses={200: PaymentSuccessSerializer()},
        manual_parameters=[
            openapi.Parameter(
                "session_id",
                openapi.IN_QUERY,
                description="ID сессии Stripe",
                type=openapi.TYPE_STRING,
            )
        ],
    )
    def get(self, request):
        session_id = request.GET.get("session_id")
        try:
            serializer = PaymentSuccessSerializer(
                {"message": f"Оплата прошла успешно! Session ID: {session_id}"}
            )
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentCancelAPIView(APIView):
    """Эндпоинт для обработки отмены оплаты. Stripe перенаправляет сюда при отмене платежа."""

    @swagger_auto_schema(
        operation_description="Обработка отмены оплаты (редирект от Stripe)",
        responses={200: PaymentCancelSerializer()},
    )
    def get(self):
        serializer = PaymentCancelSerializer(
            {"message": "Оплата отменена. Вы можете попробовать снова."}
        )
        return Response(serializer.data)
