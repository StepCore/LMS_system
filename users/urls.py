from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from materials.apps import MaterialsConfig
from users.views import UserCreateView, SubscriptionAPIView

app_name = MaterialsConfig.name

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="register"),
    path(
        "login/",
        TokenObtainPairView.as_view(permission_classes=(AllowAny,)),
        name="login",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(permission_classes=(AllowAny,)),
        name="token_refresh",
    ),
    path("subscription/", SubscriptionAPIView.as_view(), name="subscription"),
]
