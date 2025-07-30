from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .filters import PaymentFilter
from .models import Payment, User
from .serializers import PaymentSerializer, UserSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]  # Сортировка по умолчанию
    permission_classes = [permissions.AllowAny]  # Разрешаем доступ всем

    def get_queryset(self):
        """Возвращаем все платежи или только для авторизованного пользователя"""
        queryset = Payment.objects.select_related("user", "paid_course", "paid_lesson")

        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permissions_classes = (AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()
