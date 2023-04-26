from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from accounts import messages
from accounts.models import User, Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=128, min_length=6, write_only=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'tokens']

    def create(self, validated_data):
        self.user = get_user_model().objects.create_user(**validated_data)
        self.user.save()
        return self.user

    def get_tokens(self, obj):
        user = get_user_model().objects.get(email=self.user.email)

        return {
            'access': user.tokens()['access'],
            'refresh': user.tokens()['refresh'],
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = get_user_model().objects.get(email=obj['email'])

        return {
            'access': user.tokens()['access'],
            'refresh': user.tokens()['refresh']
        }

    class Meta:
        model = User
        fields = ['email', 'password', 'tokens']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        user = auth.authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed('Вы ввели неправильный логин или пароль!')
        if not user.is_active:
            raise AuthenticationFailed('Аккаунт отключен, обратитесь к администратору')
        return super().validate(attrs)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        error_messages={'blank': messages.ENTER_REFRESH_TOKEN}
    )

    default_error_messages = {'bad_token': messages.TEXT_UNAUTHORIZED}

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField

    class Meta:
        model = get_user_model()
        fields = [
            'id', 'is_superuser', 'is_staff', 'is_active', 'email', 'created_at', 'updated_at'
        ]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name', 'avatar', 'language', 'color_theme', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class RequestPasswordResetEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3, required=True)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = get_user_model()
        fields = ['email', 'redirect_url']


class PasswordTokenCheckSerializer(serializers.ModelSerializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ['uidb64', 'token']


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True, required=True)
    token = serializers.CharField(min_length=1, write_only=True, required=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True, required=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):  # noqa
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('Reset link is invalid', 401)

            user.set_password(password)
            user.save()
        except Exception:
            raise AuthenticationFailed('Reset link is invalid', 401)
        return super().validate(attrs)
