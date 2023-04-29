from django.urls import path
from .views import register,login,users,one_user,refresh,logout,verify,one_user_by_username
urlpatterns = [
    path('register',register),
    path('login',login),
    path('users',users),
    path('user/<str:user_uid>',one_user),
    path('user_u/<str:username>',one_user_by_username),
    path('logout',logout),
    path('validate',verify),
    path('refresh',refresh),
]