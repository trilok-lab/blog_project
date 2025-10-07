import os
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from twilio.rest import Client
import stripe
from .models import Verification
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer


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
            return Response({'status': 'verified'})
    except Verification.DoesNotExist:
        pass
    return Response({'status': 'invalid'}, status=400)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stripe_create_intent(request):
    stripe.api_key = os.getenv('STRIPE_API_KEY', '')
    try:
        intent = stripe.PaymentIntent.create(amount=500, currency='usd', automatic_payment_methods={'enabled': True})
        return Response({'client_secret': intent['client_secret']})
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


