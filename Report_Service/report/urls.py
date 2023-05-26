from django.urls import path
from .views import report_by_users,report_by_hotels,report_by_booking,report_by_payments

urlpatterns = [
    path('booking', report_by_booking), 
    path('users', report_by_users),
    path('paymenteffec',report_by_payments),
    path('hotels', report_by_hotels),
]
