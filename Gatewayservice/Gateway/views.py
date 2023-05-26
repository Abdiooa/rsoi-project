from django.shortcuts import render
import requests
from rest_framework.exceptions import AuthenticationFailed
from django.core.paginator import Paginator,EmptyPage
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from .forms import UserRegistrationForm,LoginForm,NewHotel,DeleteHotel,NewUser
from django.http import HttpResponseRedirect, JsonResponse
import json
import datetime
import jwt
import ast
from random import choices
from string import ascii_letters, digits
import aiohttp
from confluent_kafka import Producer
from Gatewayservice.settings import SECRET_KEY,JWT_KEY
from adrf.decorators import api_view
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import asyncio
import re
import time
import sys

from time import sleep
from django.shortcuts import redirect
import time
import pytz
from datetime import datetime as dt
tz_MOS = pytz.timezone('Europe/Moscow')

conf = {
    'bootstrap.servers': '104.248.197.192:9092,134.209.199.44:9092', 
    'session.timeout.ms': 6000,
    'group.id': 'dmqj25d74voir-consumer',
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}




def pay_room(request, paymentUid):
    start_time = time.time()
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if request.method == 'POST':
        booking = requests.get("http://reservationsvc:8070/api/v1/reservations/{}"
                            .format(request.POST['reservationUid']), cookies=session.cookies).json()
        hotel = requests.get("http://reservationsvc:8070/api/v1/hotel/{}"
                            .format(booking['hotel_uid']), cookies=session.cookies).json()
        payment = requests.get("http://paymentsvc:8060/api/v1/payment/{}"
                            .format(booking['paymentUid']), cookies=session.cookies).json()
        
        date_start = datetime.datetime.strptime(booking['startDate'], "%Y-%m-%d")
        date_end = datetime.datetime.strptime(booking['endDate'], "%Y-%m-%d")
        period = date_end - date_start
        totalcost = int(hotel['price']) * (period.days)
        pay = requests.post("http://paymentsvc:8060/api/v1/payment/pay/{}"
                            .format(paymentUid), json={'price': totalcost}, cookies=request.COOKIES)
        payedpayment = requests.get("http://paymentsvc:8060/api/v1/payment/{}"
                            .format(booking['paymentUid']), cookies=session.cookies).json()
        if pay.status_code == 200:
            q_effectued_payment ={"paymentUid":payedpayment['paymentUid'],"user_uid":data["user_uid"],"email":data['email'],"username":data["username"],'name':hotel['name'],'reservationUid':booking['reservationUid'],"hotel_uid":hotel["hotel_uid"],"Payed Price":payedpayment['price'],"status":payedpayment['status'],"address":hotel["address"],"country":hotel["country"],"city":hotel["city"]}
            producer(q_effectued_payment,"effecpayment-statistic")
            response = HttpResponseRedirect('/booking_info/{}'.format(request.POST['reservationUid']))
            booking_all = requests.get("http://reservationsvc:8070/api/v1/reservations", cookies=session.cookies)
            if booking_all.status_code != 200:
                return JsonResponse(booking_all.json(), status=status.HTTP_400_BAD_REQUEST)
            len_booking = booking_all.json()
            l_status = requests.get("http://loyaltysvc:8050/api/v1/loyalty/balance", cookies=session.cookies)
            if l_status.status_code != 200:
                return JsonResponse(l_status.json(), status=status.HTTP_400_BAD_REQUEST)
            l_status = l_status.json()['status']
            if 1 < len(len_booking) < 35 and l_status == 'None':  # BRONZE
                loyaltyUP = requests.patch("http://loyaltysvc:8050/api/v1/loyalty/edit", json={"active": "UP"},
                                        cookies=session.cookies)
                if loyaltyUP.status_code != 200:
                    return JsonResponse(loyaltyUP.json(), status=status.HTTP_400_BAD_REQUEST)
            elif 35 < len(len_booking) < 50 and l_status == 'BRONZE':  # SILVER
                loyaltyUP = requests.patch("http://loyaltysvc:8050/api/v1/loyalty/edit", json={"active": "UP"},
                                        cookies=session.cookies)
                if loyaltyUP.status_code != 200:
                    return JsonResponse(loyaltyUP.json(), status=status.HTTP_400_BAD_REQUEST)
            elif 50 < len(len_booking) and l_status == 'SILVER':  # GOLD
                loyaltyUP = requests.patch("http://loyaltysvc:8050/api/v1/loyalty/edit", json={"active": "UP"},
                                        cookies=session.cookies)
                if loyaltyUP.status_code != 200:
                    return JsonResponse(loyaltyUP.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            error = "Failed to pay!"
            response = render(request, 'user_booking.html',
                    {'booking': booking, 'hotel': hotel, 'payment': payment, 'error': error, 'user': data, \
                    'totalcost': request.POST['totalcost']})

        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
            if is_authenticated else response.delete_cookie('jwt')
        end_time = time.time()
        elapsed_time = end_time - start_time
        return response


async def del_booking(request, reservationUid):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if request.method == "POST":
        book = ast.literal_eval(request.POST['booking'])
        hot = ast.literal_eval(request.POST['hotel'])
        pay = ast.literal_eval(request.POST['payment'])
        if request.POST['status'] == "NEW":
            delbook = requests.delete("http://reservationsvc:8070/api/v1/reservations/canceled/{}"
                                    .format(reservationUid), cookies=request.COOKIES)
            if delbook.status_code == 200:
                success = "Booking deleted"
                response = render(request, 'user_booking.html', {'bookdel': success, 'user': data})
            else:
                error = "Something went wrong, please try again"
                response = render(request, 'user_booking.html', {'booking': book, 'hotel': hot,
                                                                'payment': pay, 'error': error, 'user': data})
        else:
            booking = requests.get("http://reservationsvc:8070/api/v1/reservations/{}"
                            .format(reservationUid), cookies=session.cookies).json()
            hotel = requests.get("http://reservationsvc:8070/api/v1/hotel/{}"
                            .format(booking['hotel_uid']), cookies=session.cookies).json()
            date_start = datetime.datetime.strptime(booking['startDate'], "%Y-%m-%d")
            date_end = datetime.datetime.strptime(booking['endDate'], "%Y-%m-%d")
            period = date_end - date_start
            totalcost = int(hotel['price']) * (period.days)
            payment = requests.post("http://paymentsvc:8060/api/v1/payment/reversed/{}"
                                    .format(booking['paymentUid']), json={'price': totalcost}, cookies=request.COOKIES)
            if payment.status_code == 200:
                delbook = requests.delete("http://reservationsvc:8070/api/v1/reservations/canceled/{}"
                                        .format(reservationUid), cookies=request.COOKIES)
                if delbook.status_code == 200:
                    success = "Booking deleted"
                    response = render(request, 'user_booking.html', {'bookdel':success, 'user': data})
                else:
                    error = "Booking cancellation error"
                    response = render(request, 'user_booking.html', {'booking': book, 'hotel': hot,
                                                                    'payment': pay, 'error': error, 'user': data})
            else:
                error = "Refund error"
                response = render(request, 'user_booking.html', {'booking': book, 'hotel': hot,
                                                                'payment': pay, 'error': error, 'user': data})

        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
            if is_authenticated else response.delete_cookie('jwt')
        return response

async def add_booking(request):
    is_authenticated, request, session = cookies(request)
    user = auth(request)
    if request.method == 'POST':
        data = request.POST
        startDate = datetime.datetime.strptime(request.POST['startDate'], "%Y-%m-%d")
        endDate = datetime.datetime.strptime(request.POST['endDate'], "%Y-%m-%d")
        async with aiohttp.ClientSession(cookies=request.COOKIES) as client_session:
            hotel_task = client_session.get("http://reservationsvc:8070/api/v1/hotel/{}"
                        .format(request.POST['hotel_uid']))
            user_loyalty_task = client_session.get(f"http://loyaltysvc:8050/api/v1/loyalty/status/{user['username']}")
            hotel_response,userloyalty_res = await asyncio.gather(hotel_task,user_loyalty_task)
            hotel = await hotel_response.json()
            user_loyalty = await userloyalty_res.json()
        if  startDate > endDate or startDate < datetime.datetime.now():
            dateerror = "Invalid date entry"
            response = render(request, 'hotel_info.html', {'dateerror': dateerror, 'hotel_info': hotel,
                                                    'user': user})
        else:
            async with aiohttp.ClientSession(cookies=request.COOKIES) as client_session:
                booking_response = await client_session.post("http://reservationsvc:8070/api/v1/reservations",
                                    json={"hotel_uid": data["hotel_uid"],
                                        "startDate": data["startDate"],
                                        "endDate": data["endDate"],
                                        "username": user["username"],
                                        "price": int(data["price"])})
                booking = await booking_response.json()
                if booking_response.status == 200:
                    payment_response = await client_session.get(f"http://paymentsvc:8060/api/v1/payment/{booking['paymentUid']}")
                    payment = await payment_response.json()
                    q_booking = {"reservationUid":booking['reservationUid'],"hotel_uid":booking['hotel_uid'],"user_uid":user['user_uid'],"paymentUid":booking['paymentUid'],"startDate":booking["startDate"],"endDate":booking['endDate'],"status":booking['status'],"price":payment['price'],"name":hotel['name'],"country":hotel['country'],"city":hotel['city'],"address":hotel['address'],"username":user['username'],'email':user['email'],"status_loyalty":user_loyalty['status'],"discount":user_loyalty['discount']}
                    producer(q_booking, 'payment-statistic')
                    response = HttpResponseRedirect('/booking_info/{}'.format(booking['reservationUid']))
                else:
                    error = "Something went wrong. Please try again later."
                    response = render(request, 'hotel_info.html', {'error': error, 'user': user})
        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
            if is_authenticated else response.delete_cookie('jwt') 
        return response


async def index(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    async with aiohttp.ClientSession() as client_session:
        cities_task =  client_session.get("http://reservationsvc:8070/api/v1/cities")
        _allhotels_task = client_session.get("http://reservationsvc:8070/api/v1/hotels", cookies=request.COOKIES)
        cities,_allhotels = await asyncio.gather(cities_task,_allhotels_task)
        cities = await cities.json()
        _allhotels = await _allhotels.json()
        if len(_allhotels) != 0:
            title = "Amazing Shareton Hotels"
            paginator = Paginator(_allhotels, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            response = render(request, 'index.html', {'allhotels': _allhotels, 'cities': cities, 'page_obj': page_obj,
                                            'title': title, 'user': data})
        else:
            title = "No hotels :("
            response = render(request, 'index.html', {'title': title, 'cities': cities, 'user': data})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response

async def balance(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    try:
        async with aiohttp.ClientSession(cookies=request.COOKIES) as client_session:
            loyalty_task = client_session.get(f"http://loyaltysvc:8050/api/v1/loyalty/status/{data['username']}")
            user_task = client_session.get(f"http://sessionsvc:8040/api/v1/session/user/{data['user_uid']}")
            _allbook_task = client_session.get("http://reservationsvc:8070/api/v1/reservations")

            loyalty_res, user_res, _allbook_res = await asyncio.gather(loyalty_task, user_task, _allbook_task)

            loyalty = await loyalty_res.json()
            user = await user_res.json()
            _allbook = await _allbook_res.json()

            sort = sorted(_allbook, key=lambda x: (x['startDate'], x['endDate']), reverse=True)
            curr, hist, currhotel, histhotel, currpay, histpay = ([] for _ in range(6))

            payment_tasks = []
            hotels_task = []
            
            for s in sort:
                payment_task = client_session.get(f"http://paymentsvc:8060/api/v1/payment/{s['paymentUid']}")
                hotel_task = client_session.get(f"http://reservationsvc:8070/api/v1/hotel/{s['hotel_uid']}")
                payment_tasks.append(payment_task)
                hotels_task.append(hotel_task)
            
            payments = []
            for payment_task in asyncio.as_completed(payment_tasks):
                payment = await payment_task
                payments.append(await payment.json())
                
            hotels = []
            for hotel_task in asyncio.as_completed(hotels_task):
                hotel = await hotel_task
                hotels.append(await hotel.json())
                
            for index, s in enumerate(sort):
                hotel = hotels[index]
                payment = payments[index]
                if datetime.datetime.strptime(s['endDate'], "%Y-%m-%d") > datetime.datetime.now():
                    if payment['status'] == 'NEW' or payment['status'] == 'PAID':
                        curr.append(s)
                        currhotel.append(hotel)
                        currpay.append(payment)
                    else:
                        hist.append(s)
                        histhotel.append(hotel)
                        histpay.append(payment)
            currbookhot = zip(curr, currhotel, currpay)
            histbookhot = zip(hist, histhotel, histpay)
            response = render(request, 'balance.html', {'loyalty': loyalty, 'user': user, 'currbookhot': currbookhot,
                                                        'cities': cities, 'histbookhot': histbookhot})
    except Exception as e:
        usererror = "The data could not be displayed. Try again later"
        response = render(request, 'balance.html', {'user': data, 'cities': cities, 'usererror': usererror})
        print(f"Error: {e}")

    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response


async def all_users(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if data['role'] != 'admin':
        response = HttpResponseRedirect('/index')
        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True)
        return response
    async with aiohttp.ClientSession() as client_session:
        async with client_session.get("http://sessionsvc:8040/api/v1/session/users", cookies=request.COOKIES) as _users_res:
            _users = await _users_res.json()
    response = render(request, 'all_users.html', {'all_users': _users, 'user': data})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response
    return response

def cities(request):
    dict_cities = requests.get("http://reservationsvc:8070/api/v1/cities")
    if dict_cities.status_code == 200:
        dict_cities = dict_cities.json()
        return JsonResponse(dict_cities, status=status.HTTP_200_OK, safe=False)
    return JsonResponse({"detail": "No content"}, status=status.HTTP_204_NO_CONTENT)

def admin(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if data['role'] != 'admin':
        response = HttpResponseRedirect('/index')
        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True)
        return response
    response = render(request, 'admin.html', {'user': data})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response


def delete_hotel_admin(request):
    start_time = time.time()
    error = None
    is_authenticated, request, session = cookies(request)
    data = auth(request)

    if request.method == "GET":
        form = DeleteHotel()
    if request.method == "POST":
        form = DeleteHotel(data=request.POST)
        new_hotel = requests.delete('http://reservationsvc:8070/api/v1/hotel/{}'.format(form.data['hotelUid']),
                                    cookies=request.COOKIES)
        error = 'success'
        if new_hotel.status_code != 204:
            try:
                error = new_hotel.json()['message']
            except Exception:
                error = 'Parse error'
    response = render(request, 'delete_hotel.html', {'form': form, 'user': data, 'error': error})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"index() executed in {elapsed_time:.4f} seconds")
    return response



async def fetch(url,cookies=None):
    async with aiohttp.ClientSession(cookies=cookies) as client_session:
        async with client_session.get(url) as response:
            return await response.json()

async def hotel_info(request,hotelUid):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    cities_task = fetch("http://reservationsvc:8070/api/v1/cities")
    hotel_task = fetch("http://reservationsvc:8070/api/v1/hotel/{}".format(hotelUid), cookies=request.COOKIES)
    try:
        cities,hotel = await asyncio.gather(cities_task,hotel_task)
        error = None
        new_data = {'hotel_info': hotel, 'cities': cities, 'user': data, 'error': error}
        response = render(request, 'hotel_info.html', new_data)
    except:
        error = "Failed to display hotel information. Please try again later."
        response = render(request, 'hotel_info.html', {'error': error, 'cities': None, 'user': None})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response


async def registration(request):
    error = None
    form = UserRegistrationForm()
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.data['password'] != form.data['password2']:
            return render(request,'signup.html',{'form': form, 'error': 'Password mismatch'})
        if not re.compile("^([A-Za-z0-9]+)+$").match(form.data['username']):
            return render(request, 'signup.html', {'form': form, 'error': 'No valid login'})
        async with aiohttp.ClientSession() as session:
            data = {"username": form.data['username'], "name": form.data['first_name'],
                    "last_name": form.data['last_name'], "password": form.data['password'],
                    "email": form.data['email']}
            async with session.post('http://sessionsvc:8040/api/v1/session/register', json=data) as response:
                requete = await response.json()
                error = 'success'
                if response.status != 200:
                    content = await response.text()
                    content = content.replace("'", '"')
                    error = "email is not unique" if 'email' in content else "username is not unique"
            datat = {"username":requete['username']}
            q_session = {"username": requete["username"], "detail": 'Register',
                "date": dt.now(tz_MOS).strftime('%Y-%m-%d %H:%M:%S %Z%z')}
            producer(q_session, 'users-statistic')
            async with session.post("http://loyaltysvc:8050/api/v1/loyalty/create", json=datat) as response:
                if response.status != 200:
                    return JsonResponse(await response.json(), status=status.HTTP_400_BAD_REQUEST)
        return HttpResponseRedirect('/login')
    return render(request, 'signup.html', {'form': form, 'error': error})

async def make_logout(request):
    async with aiohttp.ClientSession() as client_session:
        async with client_session.post("http://sessionsvc:8040/api/v1/session/logout", cookies=request.COOKIES) as res:
            data = await res.json()
    if res.status == 200:
        q_session = {"username": data["username"], "detail": 'Logout',
                "date": dt.now(tz_MOS).strftime('%Y-%m-%d %H:%M:%S %Z%z')}
        producer(q_session, 'users-statistic')
        response = HttpResponseRedirect('/login')
        response.delete_cookie('jwt')
        return response
    return render(request,'login.html')

def static_booking(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if data['role'] != 'admin':
        response = HttpResponseRedirect('/index')
        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True)
        return response
    try:
        static_books = requests.get("http://reportssvc:8030/api/v1/reports/booking", cookies=request.COOKIES).json()
        dictlist = list()
        for key,value in static_books.items():
            temp = [key,value]
            dictlist.append(temp)
    except Exception:
        dictlist = None
    print(dictlist)
    response = render(request, 'static_booking.html', {'static_bookings': dictlist, 'user': data})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response

def users_static(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if data['role'] != 'admin':
        response = HttpResponseRedirect('/index')
        response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True)
        return response
    try:
        static_users = requests.get("http://reportssvc:8030/api/v1/reports/users", cookies=request.COOKIES).json()
        dictlist = list()
        for key, value in static_users.items():
            temp = [key, value]
            dictlist.append(temp)
    except Exception:
        dictlist = None
    response = render(request, 'users_static.html', {'all_users': dictlist, 'user': data})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response

def static_payments(request):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if data['role']!= 'admin':
        response = HttpResponseRedirect('/index')
        response.set_cookie(key='jwt',value=session.cookies.get('jwt'),httponly=True)
        return response
    try:
        static_payments = request.get("http://reportssvc:8030/api/v1/reports/paymenteffec", cookies=request.COOKIES).json()
        dictlist = list()
        for key, value in static_payments.items():
            temp = [key,value]
            dictlist.append(temp)
    except Exception:
        dictlist = None
    response = render(request,'payments_static.html',{'all_payments':dictlist,'user':data})
    response.set_cookie(key='jwt',value=session.cookies.get('jwt'),httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response


def make_login(request):
    error = None
    if request.method == "GET":
        form = LoginForm()
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        session = requests.post('http://sessionsvc:8040/api/v1/session/login',
                                json={"username": request.POST.get('username'),
                                    "password": request.POST.get('password')})
        if session.status_code == 200:
            q_session = session.json()
            q_session.update({"username": request.POST["username"],
                    "date": dt.now(tz_MOS).strftime('%Y-%m-%d %H:%M:%S %Z%z')})
            producer(q_session, 'users-statistic')
            response = HttpResponseRedirect('/index')
            response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True)
            return response
        else:
            session = session.content.decode('utf8').replace("'", '"')
            error = json.loads(session)['detail']
    return render(request, 'login.html', {'form': form, 'error': error, 'cities': cities})


async def add_hotel_admin(request):
    error = None
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    
    if request.method == "GET":
        form = NewHotel()
    if request.method == "POST":
        form = NewHotel(data=request.POST)
        error = 'success'
        async with aiohttp.ClientSession() as client_session:
            async with client_session.post("http://reservationsvc:8070/api/v1/hotels",
                                json={'name': form.data['name'], 'country': form.data['country'],
                                        'stars': form.data['stars'], 'price': form.data['price'],
                                        'city': form.data['city'],
                                        'address': form.data['address']},
                                cookies=request.COOKIES) as res:
                new_hotel = await res.json()
        if res.status != 200:
            error = "errors"
    response = render(request, 'new_hotel.html', {'form': form, 'user': data, 'error': error})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response


async def add_user(request):
    error = None
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    if request.method == "GET":
        form = NewUser()
    if request.method == "POST":
        form = NewUser(data=request.POST)
        error = 'success'
        if form.is_valid():
            if not re.compile("^([A-Za-z0-9]+)+$").match(form.data['username']):
                return render(request, 'signup.html', {'form': form, 'error': 'No valid login'})
            async with aiohttp.ClientSession() as client_session:
                async with client_session.post("http://sessionsvc:8040/api/v1/session/register",json={
                                        'name': form.data['name'],
                                        "last_name": form.data['last_name'],
                                        'username': form.data['username'],
                                        'password': form.data['password'],
                                        'email': form.data['email'],
                                        'role': form.data['role']
                                    },
                                    cookies=request.COOKIES) as res:
                    new_user = await res.json()
            if res.status != 200:
                error = "errors"
        else:
            error = "errors"
    response = render(request, 'new_user.html', {'form': form, 'user': data, 'error': error})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response

async def booking_info(request,reservationUid):
    is_authenticated, request, session = cookies(request)
    data = auth(request)
    try:
        async with aiohttp.ClientSession(cookies=request.COOKIES) as client_session:
            cities_task = client_session.get("http://reservationsvc:8070/api/v1/cities")
            booking_task = client_session.get("http://reservationsvc:8070/api/v1/reservations/{}"
                            .format(reservationUid))
            
            cities_res, booking_res = await asyncio.gather(cities_task,booking_task)
            
            cities = await cities_res.json()
            booking = await booking_res.json()
            
            hotel_task = client_session.get("http://reservationsvc:8070/api/v1/hotel/{}"
                            .format(booking['hotel_uid']))
            payment_task = client_session.get("http://paymentsvc:8060/api/v1/payment/{}"
                            .format(booking['paymentUid']))
            
            hotel_res, payment_res = await asyncio.gather(hotel_task,payment_task)
            
            hotel = await hotel_res.json()
            payment = await payment_res.json()
            
            date_start = datetime.datetime.strptime(booking['startDate'], "%Y-%m-%d")
            date_end = datetime.datetime.strptime(booking['endDate'], "%Y-%m-%d")
            period = date_end - date_start
            totalcost = int(hotel['price']) * (period.days)
            
            response = render(request, 'user_booking.html',
                {'booking': booking, 'hotel': hotel, 'payment': payment, 'cities': cities, 'user': data,
                'totalcost': totalcost})
    except:
        bookerror = "Failed to display booking, try again"
        response = render(request, 'user_booking.html', {'bookerror': bookerror, 'cities': cities, 'user': data})
    response.set_cookie(key='jwt', value=session.cookies.get('jwt'), httponly=True) \
        if is_authenticated else response.delete_cookie('jwt')
    return response

def delivery_callback(err, msg):
    if err:
        sys.stderr.write('%% Message failed delivery: %s\n' % err)
    else:
        sys.stderr.write('%% Message delivered to %s [%d]\n' % (msg.topic(), msg.partition()))


def producer(data,topic):
    topic = topic
    
    p = Producer(**conf)
    line = str(data)
    try:
        p.produce(topic, line.rstrip(), callback=delivery_callback)
    except BufferError:
        sys.stderr.write('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(p))
    p.poll(0)

    sys.stderr.write('%% Waiting for %d deliveries\n' % len(p))
    p.flush()



def auth(request):
    token = request.COOKIES.get('jwt')
    
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    
    payload = jwt.decode(token,JWT_KEY,algorithms=['HS256'],options={"verify_exp": False})
    
    payload.pop('exp')
    payload.pop('iat')
    return payload


def cookies(request):
    is_authenticated = False
    session = requests.get("http://sessionsvc:8040/api/v1/session/validate",cookies=request.COOKIES)
    if session.status_code != 200:
        if session.status_code == 403:
            session = requests.get("http://sessionsvc:8040/api/v1/session/refresh", cookies=request.COOKIES)
            is_authenticated = True
        elif session.status_code != 401:
            pass
        else:
            request.delete_cookie('jwt')
    else:
        is_authenticated = True
    return is_authenticated,request,session
