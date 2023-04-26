from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import smart_str, smart_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status, permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import messages
from accounts.models import User, Profile
from accounts.send_email import SendEmail
from accounts.serializers import (
    RegisterSerializer, LoginSerializer, LogoutSerializer, UserDetailSerializer,
    ProfileSerializer, RequestPasswordResetEmailSerializer, PasswordTokenCheckSerializer,
    SetNewPasswordSerializer
)


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    @staticmethod
    def get_access_token(serializer):
        tokens = serializer.data.get('tokens', None)
        token = tokens.get('access', None)
        return token

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DeleteAccountView(APIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):  # noqa
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginApiView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDetailView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status.HTTP_200_OK)


class RequestPasswordResetEmailView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')

        if get_user_model().objects.filter(email=email).exists():
            user = get_user_model().objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            redirect_url = request.data.get('redirect_url')
            current_site = 'http://' + get_current_site(request=request).domain
            current_site = redirect_url if redirect_url else current_site
            reset_link = f'{current_site}?uid={uidb64}&token={token}'
            SendEmail.send_email(user.email, 'Reset your password', reset_link)
            return Response({'success': messages.TEXT_LINK_RESET_PASSWORD},
                            status=status.HTTP_200_OK)

        return Response({'error': messages.USER_NOT_EXISTS},
                        status=status.HTTP_404_NOT_FOUND)


class PasswordTokenCheckView(generics.GenericAPIView):
    serializer_class = PasswordTokenCheckSerializer

    @staticmethod
    def get_user(uidb64):  # noqa
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(id=user_id)

        except User.DoesNotExist:
            return Response({'error': messages.USER_NOT_EXISTS},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as message:
            error_type = type(message).__name__
            return Response({'error_type': f'{error_type}', 'message': f'{message}'},
                            status=status.HTTP_400_BAD_REQUEST)
        return user

    def get(self, request, *args, **kwargs):  # noqa
        try:
            uidb64 = self.kwargs.get('uidb64')
            user = self.get_user(uidb64)
            token = self.kwargs.get('token')

            if PasswordResetTokenGenerator().check_token(user, token):
                return Response({'message': messages.SUCCESS_TOKEN_AND_UID},
                                status=status.HTTP_200_OK)

            return Response({'field': 'token',
                             'message': messages.ERROR_TOKEN_AND_UID},
                            status=status.HTTP_400_BAD_REQUEST)

        except AttributeError:
            return Response({'field': 'uid',
                             'message': messages.ERROR_TOKEN_AND_UID},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as message:
            error_type = type(message).__name__
            return Response({'error_type': f'{error_type}',
                             'message': f'{message}'},
                            status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordView(generics.UpdateAPIView):
    serializer_class = SetNewPasswordSerializer
    http_method_names = ['patch', ]

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': messages.PASSWORD_RESET_SUCCESS},
                        status=status.HTTP_200_OK)


class ProfileViewSet(viewsets.GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def retrieve(self, request):
        try:
            serializer = self.serializer_class(request.user.profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({'error': messages.PROFILE_DOES_NOT_EXISTS},
                            status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request):
        try:
            serializer = self.serializer_class(request.user.profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({'error': messages.PROFILE_DOES_NOT_EXISTS},
                            status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request):
        try:
            instance = request.user.profile
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response({'error': messages.PROFILE_DOES_NOT_EXISTS},
                            status=status.HTTP_404_NOT_FOUND)
