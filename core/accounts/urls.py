from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    RegisterView, LoginApiView, LogoutAPIView, UserDetailView, DeleteAccountView, ProfileViewSet,
    RequestPasswordResetEmailView, PasswordTokenCheckView, SetNewPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('delete_user/', DeleteAccountView.as_view(), name='delete_user'),
    path('login/', LoginApiView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('user_detail/', UserDetailView.as_view(), name='user_detail'),
    path('profile/', ProfileViewSet.as_view({'get': 'retrieve', 'post': 'create', 'put': 'update', 'delete': 'destroy'}), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('request_reset_password/', RequestPasswordResetEmailView.as_view(),
         name='request_reset_password'),
    path('password_reset_confirm/<uidb64>/<token>/', PasswordTokenCheckView.as_view(),
         name='password_reset_confirm'),
    path('password_reset_complete/', SetNewPasswordView.as_view(),
         name='password_reset_complete')
]
