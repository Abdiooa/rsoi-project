from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns=[
    path('loyalty/create', create),
    path('loyalty/delete',delete),
    path('loyalty/balance',balance),
    path('loyalty/edit', edit), 
    path('loyalty/status/<str:username>', balance_static),
    path('loyalty/edit_balance',edit_balance),
    path('loyalties',Loyalties),
]