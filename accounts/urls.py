from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # pyright: ignore[reportMissingImports]
from .views import RegisterView, verify_mobile, send_otp, verify_otp, stripe_create_intent, stripe_confirm_payment, MeView, LogoutView, SocialLoginUrlView, SocialTokenSignInView, PasswordForgotView, PasswordResetConfirmView, TwilioStartView, TwilioVerifyView, StripeWebhookView, StripeStatusView
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings


def contact_view(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)
    name = request.POST.get('name') or ''
    email = request.POST.get('email') or ''
    message = request.POST.get('message') or ''
    if not message:
        return JsonResponse({'detail': 'message required'}, status=400)
    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if admin_email:
            send_mail(
                subject=f'Contact from {name or "Anonymous"}',
                message=f'From: {email or "unknown"}\n\n{message}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[admin_email],
                fail_silently=True,
            )
        return JsonResponse({'status': 'ok'})
    except Exception as exc:
        return JsonResponse({'detail': str(exc)}, status=400)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('verify-mobile/', verify_mobile, name='verify_mobile'),
    path('otp/send/', send_otp, name='send_otp'),
    path('otp/verify/', verify_otp, name='verify_otp'),
    path('stripe/create-intent/', stripe_create_intent, name='stripe_create_intent'),
    path('stripe/confirm/', stripe_confirm_payment, name='stripe_confirm_payment'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('stripe/status/<str:pi_id>/', StripeStatusView.as_view(), name='stripe_status'),
    path('contact/', contact_view, name='contact_us'),
    path('auth/social/<str:provider>/login-url/', SocialLoginUrlView.as_view(), name='social_login_url'),
    path('auth/social/<str:provider>/token/', SocialTokenSignInView.as_view(), name='social_token_signin'),
    path('password/forgot/', PasswordForgotView.as_view(), name='password_forgot'),
    path('password/reset/', PasswordResetConfirmView.as_view(), name='password_reset'),
    path('twilio/start/', TwilioStartView.as_view(), name='twilio_start'),
    path('twilio/verify/', TwilioVerifyView.as_view(), name='twilio_verify'),
]


