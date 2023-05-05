from django.shortcuts import render
from .serializers import HotelSerializer, ReservationSerializer
from rest_framework import viewsets,status
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError, NotAuthenticated
from ReservationService.settings import SECRET_KEY,JWT_KEY
import jwt
from django.forms.models import model_to_dict
from adrf.decorators import api_view
from rest_framework.response import Response
from .models import Reservation,Hotel
from django.core import serializers
from django.http import JsonResponse
import pytz
import datetime
import requests
import json
from datetime import datetime as dt
tz_MOS = pytz.timezone('Europe/Moscow')

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(tz_MOS)
    return tz_MOS.normalize(local_dt)

def aslocaltimestr(utc_dt):
    return utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S')



@api_view(['POST','GET'])
def Hotels_or_addHotel(request):
    try:
        if request.method == 'GET':
            hotels = Hotel.objects.all()
            hotels = json.loads(serializers.serialize('json',hotels))
            for hotel in hotels:
                fields = hotel['fields']
                hotel.clear()
                hotel.update(fields)
            return JsonResponse(hotels, status=status.HTTP_200_OK, safe=False)
        elif request.method == 'POST':
            data = auth(request)
            if data['role']!='admin':
                return JsonResponse({'detail': 'You are not admin!'}, status=status.HTTP_400_BAD_REQUEST)
            new_hotel = {"name": request.data["name"], "country": request.data["country"],
                "city": request.data["city"], "address": request.data["address"],
                "stars": request.data["stars"], "price": request.data["price"]}
            serializer = HotelSerializer(data=new_hotel)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return JsonResponse(serializer.data,status=status.HTTP_200_OK,safe=False,json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def filter_date(request):
    try:
        if "startDate" and "endDate" in request.data.keys():
            filter_booking = requests.get("http://reservationsvc:8070/api/v1/reservations/date/{}/{}".
                                        format(request.data["startDate"], request.data["endDate"]),
                                        cookies=request.COOKIES)
            if filter_booking.status_code == 204:
                hotels = Hotel.objects.all()
                hotels = json.loads(serializers.serialize('json', hotels))
                if "city" in request.data.keys():
                    for hotel in hotels:
                        if hotel["fields"]["city"] != request.data["city"]:
                            hotel.clear()
                hotels = [i for i in hotels if i]
                for hotel in hotels:
                    fields = hotel["fields"]
                    hotel.clear()
                    hotel.update(fields)
                return JsonResponse(hotels, status=status.HTTP_200_OK, safe=False)

        else:
            hotels = Hotel.objects.all()
            hotels = json.loads(serializers.serialize('json', hotels))
            if "city" in request.data.keys():
                for hotel in hotels:
                    if hotel["fields"]["city"] != request.data["city"]:
                        hotel.clear()
            hotels = [i for i in hotels if i]
            for hotel in hotels:
                fields = hotel["fields"]
                hotel.clear()
                hotel.update(fields)
            return JsonResponse(hotels, status=status.HTTP_200_OK, safe=False)
        if filter_booking.status_code == 200:
            filter_booking = filter_booking.json()
            hotels = Hotel.objects.all()
            hotels = json.loads(serializers.serialize('json', hotels))
            if "city" in request.data.keys():
                for hotel in hotels:
                    if hotel["fields"]["city"] != request.data["city"]:
                        hotel.clear()
            hotels = [i for i in hotels if i]
            for hotel in hotels:
                count_rooms = 0
                fields = hotel["fields"]
                hotel.clear()
                hotel.update(fields)
                if "city" in request.data.keys():
                    request = request
                if "startDate" and "endDate" in request.data.keys():
                    for booking in filter_booking:
                        if booking['hotel_uid'] in hotel['hotelUid']:
                            count_rooms += 1
            hotels = hotels
            return JsonResponse(hotels, status=status.HTTP_200_OK, safe=False)
        return JsonResponse({'message': 'No content'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def cities_hotels(request):
    try:
        cities = list(Hotel.objects.all().distinct('city').values('city'))
        json.dumps(cities)
        return JsonResponse(cities, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
def all_hotels_statics(request):
    try:
        data = auth(request)
        if 'admin' not in data['role']:
            return JsonResponse({'detail': 'You are not admin!'})
        hotel_reservations = Reservation.objects.all()
        reservations = json.loads(serializers.serialize('json', hotel_reservations))
        for res in reservations:
            payBalance = requests.get(
                "http://paymentsvc:8060/api/v1/payment/{}".format(res['fields'].get("paymentUid")),
                cookies=request.COOKIES)
            if payBalance.status_code == 200:
                payBalance = payBalance.json()
                res['fields'].update(payBalance)
            about_hotel = requests.get(
                "http://reservationsvc:8070/api/v1/hotels/{}".format(res['fields'].get("hotel_id")),
                cookies=request.COOKIES)
            if about_hotel.status_code == 200:
                about_hotel = about_hotel.json()
                res['fields'].update(about_hotel)
            user = requests.get(
                "http://sessionsvc:8040/api/v1/session/user_u/{}".format(res['fields'].get("username")),
                cookies=request.COOKIES)
            if user.status_code == 200:
                user = user.json()
                res['fields'].update(user)
            loyalty = requests.get(
                "http://loyaltysvc:8050/api/v1/loyalty/status/{}".format(res['fields'].get("username")),
                cookies=request.COOKIES)
            if loyalty.status_code == 200:
                loyalty = loyalty.json()
                res['fields'].update(loyalty)
            safe = res['fields']
            res.clear()
            res.update(safe)
        return JsonResponse(reservations, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def hotelByUuid(request,hotelUid):
    try:
        hotel=Hotel.objects.get(hotelUid=hotelUid)
        serializer=HotelSerializer(hotel)
        return JsonResponse(serializer.data,status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message':'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','DELETE'])
def about_or_delete(request,hotelUid):
    try:
        if request.method == 'GET':
            hotels = Hotel.objects.filter(hotelUid=hotelUid)
            if len(hotels) == 0:
                return JsonResponse({'error': 'No content'}, status=status.HTTP_400_BAD_REQUEST)
            hotels = json.loads(serializers.serialize('json', hotels))
            return JsonResponse(hotels[0]['fields'], status=status.HTTP_200_OK, safe=False)
        else:
            data = auth(request)
            if data['role']!= 'admin':
                return JsonResponse({'detail': 'You are not admin!'}, status=status.HTTP_400_BAD_REQUEST)
            hotel = Hotel.objects.get(hotelUid=hotelUid)
            hotel.delete()
            return JsonResponse({'detail': 'success deleted'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def aHotel(request,pk=None):
    try:       
        reservation=Hotel.objects.get(id=pk)
        serializer=HotelSerializer(reservation)
        return JsonResponse(serializer.data,status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message':'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)






## ---------------------------------------------------------


@api_view(['POST','GET'])
def create_or_all(request):
    try:
        data = auth(request)
        username= data['username']
        if not username:
            return JsonResponse({'message': 'Nom d utilisateur manquant dans les en-têtes de requete'}, status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'POST':
            date_start = datetime.datetime.strptime(request.data['startDate'], "%Y-%m-%d")
            date_end = datetime.datetime.strptime(request.data['endDate'], "%Y-%m-%d")
            period = date_end - date_start
            totalcost = int(request.data['price']) * (period.days)
            payBalance = requests.post("http://paymentsvc:8060/api/v1/payment/create",
                                    json={"price": totalcost}, cookies=request.COOKIES)
            if payBalance.status_code != 200:
                return JsonResponse({'error': 'Error in payment'}, status=status.HTTP_400_BAD_REQUEST)
            payBalance = payBalance.json()
            loyBalanceedit = requests.patch("http://loyaltysvc:8050/api/v1/loyalty/edit_balance",json={'status':payBalance["status"],'price':totalcost}, cookies=request.COOKIES)
            if loyBalanceedit.status_code != 200:
                return JsonResponse({'error': 'Error in loyalty'}, status=status.HTTP_400_BAD_REQUEST)
            new_reservation = {"hotel_uid": request.data["hotel_uid"], "username": username,
                            "paymentUid": payBalance["paymentUid"], "startDate": request.data["startDate"],
                            "endDate": request.data["endDate"], 'status': payBalance["status"]}
            serializer = ReservationSerializer(data=new_reservation)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return JsonResponse(serializer.data,status=status.HTTP_200_OK, safe=False)
        elif request.method == 'GET':
            reservations = Reservation.objects.filter(username=username)
            users_reservations = json.loads(serializers.serialize('json', reservations))
            for res in users_reservations:
                payBalance = requests.get(
                    "http://payementsvc:8060/api/v1/payment/{}".format(res['fields'].get("paymentUid")),
                    cookies=request.COOKIES)
                if payBalance.status_code == 200:
                    payBalance = payBalance.json()
                    res['fields'].update(payBalance)
                hotel = requests.get(
                    "http://reservationsvc:8070/api/v1/hotel/{}".format(res['fields'].get("hotel_uid")),
                    cookies=request.COOKIES)
                if hotel.status_code == 200:
                    hotel = hotel.json()
                    res['fields'].update(hotel)
                fields = res["fields"]
                res.clear()
                res.update(fields)
            return JsonResponse(users_reservations, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def about_one(request,reservationUid):
    try:
        auth(request)
        reservations = Reservation.objects.get(reservationUid=reservationUid)
        reservations = model_to_dict(reservations)
        hotel = requests.get("http://reservationsvc:8070/api/v1/hotel/{}".format(reservations["hotelUid"]),
                            cookies=request.COOKIES)
        if hotel.status_code == 200:
            hotel = hotel.json()
            reservations.update(hotel)
        payBalance = requests.get("http://paymentsvc:8060/api/v1/payment/{}".format(reservations["paymentUid"]),
                                cookies=request.COOKIES)
        if payBalance.status_code == 200:
            payBalance = payBalance.json()
            reservations.update(payBalance)
        return JsonResponse(reservations, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','DELETE'])
def upadate_get(request,reservationUid):
    if request.method == 'GET':
        try:    
            reservation=Reservation.objects.get(reservationUid=reservationUid)
            serializer=ReservationSerializer(reservation)
            return JsonResponse(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'message':'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PATCH':
        try:
            reservation=Reservation.objects.get(reservationUid=reservationUid)
            serializer=ReservationSerializer(reservation,data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return JsonResponse(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'message':'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def pay(request,reservationUid):
    try:
        auth(request)
        payment_uid = Reservation.objects.get(reservationUid=reservationUid).paymentUid
        payStatus = requests.post("http://paymentsvc:8060/api/v1/payment/pay/{}".format(payment_uid),
                                cookies=request.COOKIES)
        if payStatus.status_code == 200:
            return JsonResponse(payStatus.json(), status=status.HTTP_200_OK)
        return JsonResponse({'detail': 'NOT PAID'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def all_reservation_of_hotel(request,hotel_id):
    try:
        data = auth(request)
        if 'admin' not in data['role']:
            return JsonResponse({'detail': 'You are not admin!'})
        hotel_reservations = Reservation.objects.filter(hotel_id=hotel_id).all()
        reservations = json.loads(serializers.serialize('json', hotel_reservations))
        for res in reservations:
            payBalance = requests.get(
                "http://paymentsvc:8060/api/v1/payment/{}".format(res['fields'].get("paymentUid")),
                cookies=request.COOKIES)
            if payBalance.status_code == 200:
                payBalance = payBalance.json()
                res['fields'].update(payBalance)
            about_hotel = requests.get(
                "http://reservationsvc:8070/api/v1/hotels/{}".format(res['fields'].get("hotel_id")),cookies=request.COOKIES)
            if about_hotel.status_code == 200:
                about_hotel = about_hotel.json()
                res['fields'].update(about_hotel)
            user = requests.get(
                "http://sessionsvc:8040/api/v1/session/user_u/{}".format(res['fields'].get("username")),cookies=request.COOKIES)
            if user.status_code == 200:
                user = user.json()
                res['fields'].update(user)
            loyalty = requests.get(
                "http://loyaltysvc:8050/api/v1/loyalty/status/{}".format(res['fields'].get("username")),
                cookies=request.COOKIES)
            if loyalty.status_code == 200:
                loyalty = loyalty.json()
                res['fields'].update(loyalty)
            safe = res['fields']
            res.clear()
            res.update(safe)
        return JsonResponse(reservations, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def canceled(request,reservationUid):
    try:
        auth(request)
        print("entrerrrr")
        payment_uid = Reservation.objects.get(reservationUid=reservationUid).paymentUid
        payStatus = requests.delete("http://paymentsvc:8060/api/v1/payment/close/{}".format(payment_uid),
                                    cookies=request.COOKIES)
        if payStatus.status_code == 200:
            return JsonResponse(payStatus.json(), status=status.HTTP_200_OK)
        return JsonResponse({'detail': 'NOT CANCELED'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def filter_booking(request,startDate,endDate):
    try:
        reservations = list(Reservation.objects.filter(startDate__gte=startDate, endDate__lte=endDate).values())
        if len(reservations) == 0:
            return JsonResponse({'message': 'No content'}, status=status.HTTP_204_NO_CONTENT)
        for res in reservations:
            payBalance = requests.get(
                "http://paymentsvc:8060/api/v1/payment/{}".format(res["paymentUid"]),cookies=request.COOKIES)
            if payBalance.status_code == 200:
                payBalance = payBalance.json()
                if payBalance["status"] == "CANCELED":
                    res.clear()
        mylist = [i for i in reservations if i]
        return JsonResponse(mylist, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

def auth(request):
    token = request.COOKIES.get('jwt')
    
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    
    payload = jwt.decode(token,JWT_KEY,algorithms=['HS256'],options={"verify_exp": False})
    
    payload.pop('exp')
    payload.pop('iat')
    return payload