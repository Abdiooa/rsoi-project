from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns=[
    path('hotels',Hotels_or_addHotel),
    path('hotels/<str:pk>',aHotel),
    path('hotel/<str:hotelUid>',about_or_delete),
    path('cities',cities_hotels),
    path('hotel/date',filter_date),
    # path('hotels/<str:hotel_id>', all_reservation_of_hotel),
    path('hotels/static', all_hotels_statics),
]