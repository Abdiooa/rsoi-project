import json
from django.shortcuts import render
import requests
from django.core.paginator import Paginator,EmptyPage
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
import json
import aiohttp
from rest_framework.exceptions import AuthenticationFailed
from confluent_kafka import Consumer, KafkaException, KafkaError
from rest_framework.decorators import api_view
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import asyncio
from datetime import datetime
from time import sleep
from django.shortcuts import redirect
import time
import jwt
from Report_Service.settings import JWT_KEY
import sys
import random
import string

conf = {
    'bootstrap.servers': '104.248.197.192:9092,134.209.199.44:9092', 
    'session.timeout.ms': 6000,
    'group.id': 'dmqj25d74voir-consumer',
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}

@api_view(['GET'])
def report_by_booking(request):
    try:
        auth(request)
        data = consumer('payment-statistic')
        if len(data) != 0:
            dictOfList = {i: data[i] for i in range(0, len(data))}
            return JsonResponse(dictOfList, status=status.HTTP_200_OK,safe=False,json_dumps_params={'ensure_ascii': False})
        return JsonResponse({"message": "No content"},status=status.HTTP_204_NO_CONTENT,safe=False)
    except Exception as e:
        return JsonResponse({'message':'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def report_by_payments(request):
    try:
        auth(request)
        data = consumer('effecpayment-statistic')
        if len(data)!=0:
            dictOfList = {i:data[i] for i in range(0,len(data))}
            return JsonResponse(dictOfList,status=status.HTTP_200_OK,safe=False,json_dumps_params={'ensure_ascii': False})
        return JsonResponse({"message":"No Content"},status=status.HTTP_204_NO_CONTENT,safe=False)
    except Exception as e:
        return JsonResponse({"message":'{}'.format(e)},status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def report_by_users(request):
    try:
        auth(request)
        data = consumer('users-statistic')
        if len(data) != 0:
            dictOfList = {i: data[i] for i in range(0, len(data))}
            return JsonResponse(dictOfList,status=status.HTTP_200_OK)
        return JsonResponse({"message": "No content"}, status=status.HTTP_204_NO_CONTENT, safe=False)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def report_by_hotels(request):
    try:
        auth(request)
        hotels = requests.get("https://reservationsvc:8070/api/v1/reservations/static", cookies=request.COOKIES)
        if hotels.status_code == 200:
            hotels = hotels.content.decode('utf8').replace("'", '"')
            hotels = json.loads(hotels)
            return JsonResponse(hotels, safe=False, status=status.HTTP_200_OK)
        return JsonResponse({"detail": "No content in queue"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)



def bytes_to_json(byte):
    my_json = byte.decode('utf8').replace("'", '"')
    data = json.loads(my_json)
    return data

def auth(request):
    token = request.COOKIES.get('jwt')
    
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    
    payload = jwt.decode(token,JWT_KEY,algorithms=['HS256'],options={"verify_exp": False})
    
    payload.pop('exp')
    payload.pop('iat')
    return payload



def consumer(topic):
    resp = list()
    topics = ['{}'.format(topic)]
    
    c = Consumer(**conf)
    c.subscribe(topics)
    
    try:
        i = 0
        while True:
            msg = c.poll(timeout=1.0)
            if msg is None and i < 10:
                i += 1
                continue
            
            if i >= 10:
                c.close()
                return resp
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                    (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                                (msg.topic(), msg.partition(), msg.offset(),
                                str(msg.key())))
                byte = msg.value()
                resp.append(bytes_to_json(byte))
                i = 0
    except KeyboardInterrupt:
        sys.stderr.write('%% Aborted by user\n')
        
        c.close()
        return resp
