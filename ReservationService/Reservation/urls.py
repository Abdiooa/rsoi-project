from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns=[
    path('reservations',create_or_all),
    path('reservations/<str:reservationUid>',upadate_get),
    path('reservations/canceled/<str:reservationUid>', canceled),
    path('reservations/date/<str:startDate>/<str:endDate>', filter_booking),
    # path('hotels/<str:hotel_id>', all_reservation_of_hotel),
]