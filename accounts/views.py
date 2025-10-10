import os
from urllib.parse import urlencode
from rest_framework import generics, permissions, views, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client
import stripe
from .models import Verification
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        mobile = user.mobile_no
        if mobile:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
            from_number = os.getenv('TWILIO_FROM_NUMBER', '')
            if account_sid and auth_token and from_number:
                try:
                    client = Client(account_sid, auth_token)
                    client.messages.create(
                        body='Your verification code is 123456',
                        from_=from_number,
                        to=mobile,
                    )
                except Exception:
                    pass


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_mobile(request):
    # Placeholder: accept code and set is_mobile_verified
    code = request.data.get('code')
    mobile = request.data.get('mobile_no')
    try:
        user = User.objects.get(mobile_no=mobile)
        if code == '123456':
            user.is_mobile_verified = True
            user.save()
            return Response({'status': 'verified'})
    except User.DoesNotExist:
        pass
    return Response({'status': 'invalid'}, status=400)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_otp(request):
    mobile = request.data.get('mobile_no')
    purpose = request.data.get('purpose', 'register')
    code = '123456'
    if not mobile:
        return Response({'detail': 'mobile_no required'}, status=400)
    try:
        ver = Verification.objects.create(mobile_no=mobile, purpose=purpose, code=code)
        account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        if account_sid and auth_token and from_number:
            try:
                client = Client(account_sid, auth_token)
                client.messages.create(body=f'Your verification code is {code}', from_=from_number, to=mobile)
            except Exception:
                pass
        return Response({'status': 'sent'})
    except Exception:
        return Response({'status': 'error'}, status=400)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    mobile = request.data.get('mobile_no')
    purpose = request.data.get('purpose', 'register')
    code = request.data.get('code')
    try:
        ver = Verification.objects.filter(mobile_no=mobile, purpose=purpose).latest('created_at')
        if ver.code == code:
            ver.is_verified = True
            ver.save()
            # If verifying registration, mark the corresponding user as verified and activate
            if purpose == 'register' and mobile:
                try:
                    user = User.objects.get(mobile_no=mobile)
                    user.is_mobile_verified = True
                    user.is_active = True
                    user.save(update_fields=['is_mobile_verified', 'is_active'])
                except User.DoesNotExist:
                    pass
            return Response({'status': 'verified'})
    except Verification.DoesNotExist:
        pass
    return Response({'status': 'invalid'}, status=400)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stripe_create_intent(request):
    stripe.api_key = os.getenv('STRIPE_API_KEY', '')
    try:
        intent = stripe.PaymentIntent.create(
            amount=500,
            currency='usd',
            automatic_payment_methods={'enabled': True},
            metadata={'user_id': str(request.user.id)},
        )
        return Response({'client_secret': intent['client_secret'], 'id': intent['id']})
    except Exception as exc:
        return Response({'detail': str(exc)}, status=400)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stripe_confirm_payment(request):
    # Client confirms payment on-device; we just mark capability
    user = request.user
    user.can_submit_articles = True
    user.save(update_fields=['can_submit_articles'])
    return Response({'status': 'ok'})
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # If SimpleJWT blacklist is enabled, we could blacklist here.
        return Response({'status': 'logged_out'})


class SocialLoginUrlView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, provider):
        # Provide a simple constructed URL for client to open (demo/dev). In production use social-auth.
        redirect_uri = request.query_params.get('redirect_uri') or os.getenv('SOCIAL_REDIRECT_URI', '')
        client_id = os.getenv(f'{provider.upper()}_CLIENT_ID', '')
        base_urls = {
            'google': 'https://accounts.google.com/o/oauth2/v2/auth',
            'facebook': 'https://www.facebook.com/v17.0/dialog/oauth',
        }
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'email profile',
        }
        url = base_urls.get(provider, '')
        if not url or not client_id or not redirect_uri:
            return Response({'detail': 'provider not configured'}, status=400)
        return Response({'login_url': f"{url}?{urlencode(params)}"})


class SocialTokenSignInView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, provider):
        # In a real app, validate token/id_token with provider API.
        # For testing, accept email/name and create user if needed.
        email = request.data.get('email')
        username = request.data.get('username') or (email.split('@')[0] if email else None)
        if not email or not username:
            return Response({'detail': 'email required'}, status=400)
        user, _created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_active': True})
        if not user.email:
            user.email = email
            user.is_active = True
            user.save(update_fields=['email', 'is_active'])
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})


class PasswordForgotView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'email required'}, status=400)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Do not leak existence
            return Response({'detail': 'ok'})
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        base_url = os.getenv('FRONTEND_URL', '') or request.build_absolute_uri('/')[:-1]
        reset_link = f"{base_url}/reset-password?uid={uidb64}&token={token}"
        try:
            send_mail(
                subject='Password reset request',
                message=f'Use this link to reset your password: {reset_link}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass
        return Response({'detail': 'ok'})


class PasswordResetConfirmView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not uidb64 or not token or not new_password:
            return Response({'detail': 'uid, token, new_password required'}, status=400)
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'invalid'}, status=400)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'invalid token'}, status=400)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'detail': 'password_updated'})


class TwilioStartView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile_no')
        purpose = request.data.get('purpose', 'register')
        if not mobile:
            return Response({'detail': 'mobile_no required'}, status=400)
        code = '123456'  # replace with random in production
        Verification.objects.create(mobile_no=mobile, purpose=purpose, code=code)
        account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        if account_sid and auth_token and from_number:
            try:
                client = Client(account_sid, auth_token)
                client.messages.create(body=f'Your verification code is {code}', from_=from_number, to=mobile)
            except Exception:
                pass
        return Response({'status': 'sent'})


class TwilioVerifyView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile_no')
        purpose = request.data.get('purpose', 'register')
        code = request.data.get('code')
        if not (mobile and code):
            return Response({'detail': 'mobile_no and code required'}, status=400)
        try:
            ver = Verification.objects.filter(mobile_no=mobile, purpose=purpose).latest('created_at')
            if ver.code == code:
                ver.is_verified = True
                ver.save(update_fields=['is_verified'])
                if purpose == 'register':
                    try:
                        user = User.objects.get(mobile_no=mobile)
                        user.is_mobile_verified = True
                        user.is_active = True
                        user.save(update_fields=['is_mobile_verified', 'is_active'])
                    except User.DoesNotExist:
                        pass
                return Response({'status': 'verified'})
        except Verification.DoesNotExist:
            pass
        return Response({'status': 'invalid'}, status=400)


class StripeWebhookView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        stripe.api_key = os.getenv('STRIPE_API_KEY', '')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        event = None
        try:
            if webhook_secret:
                event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
            else:
                event = stripe.Event.construct_from(request.data, stripe.api_key)
        except Exception:
            return Response(status=400)

        if event and event.get('type') == 'payment_intent.succeeded':
            pi = event['data']['object']
            user_id = pi.get('metadata', {}).get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    user.can_submit_articles = True
                    user.save(update_fields=['can_submit_articles'])
                except User.DoesNotExist:
                    pass
        return Response(status=200)


class StripeStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pi_id):
        stripe.api_key = os.getenv('STRIPE_API_KEY', '')
        try:
            pi = stripe.PaymentIntent.retrieve(pi_id)
            return Response({'id': pi['id'], 'status': pi['status']})
        except Exception as exc:
            return Response({'detail': str(exc)}, status=400)



