from django.urls import path
from .views import report_by_users,report_by_hotels,report_by_booking

urlpatterns = [
    path('users', report_by_users),
    path('hotels', report_by_hotels),
    path('booking', report_by_booking), 
]
