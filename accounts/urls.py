from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # pyright: ignore[reportMissingImports]
from .views import RegisterView, verify_mobile, send_otp, verify_otp, stripe_create_intent, stripe_confirm_payment


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-mobile/', verify_mobile, name='verify_mobile'),
    path('otp/send/', send_otp, name='send_otp'),
    path('otp/verify/', verify_otp, name='verify_otp'),
    path('stripe/create-intent/', stripe_create_intent, name='stripe_create_intent'),
    path('stripe/confirm/', stripe_confirm_payment, name='stripe_confirm_payment'),
]


