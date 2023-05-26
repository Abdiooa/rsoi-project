from django.shortcuts import render
from .serializers import PaymentSerializer
from rest_framework import viewsets,status
from rest_framework.response import Response
from .models import Payment
import json
import jwt
from django.core import serializers
from django.http import JsonResponse
from adrf.decorators import api_view
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError, NotAuthenticated
from PaymentService.settings import SECRET_KEY,JWT_KEY
import requests


@api_view(["GET"])
def Payments(request):
    try:
        loyalties=Payment.objects.all()
        serializer=PaymentSerializer(loyalties,many=True)
        return JsonResponse(serializer.data,status=status.HTTP_200_OK,safe=False,json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def payer(request,paymentUid):
    try:
        auth(request)
        payment = Payment.objects.get(paymentUid=paymentUid)
        payment.status = "PAID"
        pay_loyalty = requests.patch("http://loyaltysvc:8050/api/v1/loyalty/edit_balance",
                                    json={'status': payment.status, 'price': request.data['price']},
                                    cookies=request.COOKIES)
        if pay_loyalty.status_code != 200:
            return JsonResponse({'error': 'Error in loyalty'}, status=status.HTTP_400_BAD_REQUEST)
        payment.save()
        return JsonResponse({'detail': 'PAID'}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(["POST"])
def createPayment(request):
    try:
        data = auth(request)
        loyBalance = requests.get("http://loyaltysvc:8050/api/v1/loyalty/balance", cookies=request.COOKIES)
        if loyBalance.status_code != 200:
            return JsonResponse({'error': 'Error in loyalty'}, status=status.HTTP_400_BAD_REQUEST)
        loyBalance = loyBalance.json()
        if loyBalance['discount'] is None:
            loyBalance['discount'] = 0
        data.update({'status': 'NEW', 'price': int(request.data["price"]-(request.data['price']*loyBalance['discount']/100))})
        serializer = PaymentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data,status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def close(request,paymentUid):
    try:
        auth(request)
        payment = Payment.objects.get(paymentUid=paymentUid)
        payment.status = "CANCELED"
        payment.save()
        return JsonResponse({'detail': 'CANCELED'}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def reversed(request, paymentUid):
    try:
        auth(request)
        payment = Payment.objects.get(paymentUid=paymentUid)
        payment.status = "REVERSED"
        print("entrerr")
        print(payment.status)
        print(request.data['price'])
        pay_loyalty = requests.patch("http://loyaltysvc:8050/api/v1/loyalty/edit_balance",
                                    json={'status': payment.status, 'price': request.data['price']},
                                    cookies=request.COOKIES)
        if pay_loyalty.status_code != 200:
            return JsonResponse({'error': 'Error in loyalty'}, status=status.HTTP_400_BAD_REQUEST)
        payment.save()
        return JsonResponse({'detail': 'REVERSED'}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def getPayment(request,paymentUid):
    try:
        data = auth(request)
        payment=Payment.objects.get(paymentUid=paymentUid)
        serializer=PaymentSerializer(payment)
        return Response(serializer.data,status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message":'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)

def auth(request):
    token = request.COOKIES.get('jwt')
    
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    
    payload = jwt.decode(token,JWT_KEY,algorithms=['HS256'],options={"verify_exp": False})
    
    payload.pop('exp')
    payload.pop('iat')
    return payload