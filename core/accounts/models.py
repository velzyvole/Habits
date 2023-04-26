from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if email is None:
            raise TypeError('Email should have a email')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None):
        if password is None:
            raise TypeError('Password should not be none')

        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, db_index=True,
                              null=False, blank=False, verbose_name='Email address')

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    def __str__(self):
        return f'{self.id}: {self.email}'

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class Profile(models.Model):
    LANGUAGE_CHOICE = [('kz', 'kz'), ('ru', 'ru'), ('en', 'en')]
    COLOR_THEME = [('black', 'black'), ('white', 'white')]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', verbose_name='User')
    name = models.CharField(max_length=150, verbose_name='Name')
    avatar = models.ImageField(verbose_name='Avatar')
    language = models.CharField(choices=LANGUAGE_CHOICE, max_length=5, verbose_name='Language')
    color_theme = models.CharField(choices=COLOR_THEME, max_length=50, verbose_name='Color theme')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}: {self.user.email}'
