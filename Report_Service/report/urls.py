from django.urls import path
from .views import report_by_users,report_by_hotels,report_by_booking

urlpatterns = [
    path('report/booking', report_by_booking), 
    path('reports/users', report_by_users),
    path('reports/hotels', report_by_hotels),
]
