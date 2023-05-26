from django.urls import path
from .views import *
urlpatterns = [
    # VIEW
    path('index/', index, name="index"),
    path('signup', registration, name="signup"),
    path('login', make_login, name="login"),
    path('logout', make_logout, name="logout"),
    path('balance', balance, name="balance"),
    path('admin', admin, name="admin"),
    path('hotel_info/<str:hotelUid>/', hotel_info, name="hotel_info"),
    path('admin', admin, name="admin"),
    path('add-hotel', add_hotel_admin, name="add_hotel"),
    path('add-user', add_user, name="add_user"),
    path('delete-hotel', delete_hotel_admin, name="delete_hotel"),
    path('all-users', all_users, name="all_users"),
    path('add_booking', add_booking, name="add_booking"),
    path('booking_info/<str:reservationUid>', booking_info, name="booking_info"),
    path('pay_room/<str:paymentUid>', pay_room, name="pay_room"),
    path('del_booking/<str:reservationUid>', del_booking, name="del_booking"),
    path('static_booking', static_booking, name="static_booking"),
    path('static_payments', static_payments, name="static_payments"),
    path('users-static', users_static, name="users_static"),
    # path('all-booking-static', all_booking_static, name="all_booking_static"),
]