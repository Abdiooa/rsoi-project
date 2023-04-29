from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns=[
    path('payment/create',createPayment),
    path('payment/<str:paymentUid>',getPayment),
    path('payments',Payments),
    path('payment/reversed/<str:paymentUid>', reversed),
    path('payment/pay/<str:paymentUid>', payer), 
    path('payment/close/<str:paymentUid>',close),
]