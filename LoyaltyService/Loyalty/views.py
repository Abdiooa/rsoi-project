from django.shortcuts import render
from .serializers import UserLoyaltySerializer
from rest_framework import viewsets,status
from rest_framework.response import Response
from .models import UserLoyalty
import json
from django.http import JsonResponse
from django.core import serializers
from adrf.decorators import api_view
from LoyaltyService.settings import SECRET_KEY,JWT_KEY
import jwt
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError, NotAuthenticated


@api_view(['POST'])
def create(request):
    try:
        data = {"username":request.data['username'],"status": "None", "discount": 0,"reservationCount": 0,"balance":0}
        serializer = UserLoyaltySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete(request):
    try:
        data = auth(request)
        username = data['username']
        if not username:
            return JsonResponse({'message': 'Nom d utilisateur manquant dans les en-têtes de requete'}, status=status.HTTP_400_BAD_REQUEST)
        UserLoyalty = UserLoyalty.objects.get(username=username)
        UserLoyalty.delete()
        JsonResponse({'detail': 'success deleted'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def balance(request):
    try:
        data = auth(request)
        username = data['username']
        if not username:
            return JsonResponse({'message': 'Nom d utilisateur manquant dans les en-têtes de requete'}, status=status.HTTP_400_BAD_REQUEST)
        user_loyalty = UserLoyalty.objects.get(username=username)
        serializer = UserLoyaltySerializer(user_loyalty)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    except UserLoyalty.DoesNotExist:
        return JsonResponse({'message': 'Aucune fidélité trouvée pour cet utilisateur'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def edit_balance(request):
    try:
        user = auth(request)
        userLoyalty = UserLoyalty.objects.get(username=user['username'])
        if request.data['status'] == "PAID":
            print("entreer")
            print(userLoyalty.balance)
            userLoyalty.balance = userLoyalty.balance - int(request.data['price'])
            if userLoyalty.balance < 0:
                return JsonResponse({'message': '{}'.format(Exception)}, status=status.HTTP_400_BAD_REQUEST)
        elif request.data['status'] == "REVERSED":
            userLoyalty.balance = userLoyalty.balance + int(request.data['price'])
        elif request.data['status'] == "NEW":
            userLoyalty.balance = userLoyalty.balance + int(request.data['price'])
        userLoyalty.save()
        return JsonResponse({'detail': 'success edit'}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def balance_static(request, username):
    try:
        auth(request)
        userLoyalty = UserLoyalty.objects.get(username=username)
        serializer = UserLoyaltySerializer(userLoyalty)
        return JsonResponse(serializer.data,status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)
@api_view(["GET"])
def Loyalties(request):
    try:
        loyalties=UserLoyalty.objects.all()
        serializer=UserLoyaltySerializer(loyalties,many=True)
        return JsonResponse(serializer.data,status=status.HTTP_200_OK,safe=False,json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'message': '{}'.format(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
def edit(request):
    status_list = {'None': 0, "BRONZE": 5, "SILVER": 12, "GOLD": 17}
    status_key = list(status_list.keys())
    data = auth(request)
    userLoyalty = UserLoyalty.objects.get(username=data['username'])
    i = 0

    while i < len(status_key):
        if status_key[i] == userLoyalty.status:
            break
        i += 1

    if request.data['active'] == 'UP':
        if i < len(status_key) - 1:
            i += 1
    elif request.data['active'] == 'DOWN':
        if i > 0:
            i -= 1
    userLoyalty.status = status_key[i]
    userLoyalty.discount = status_list[status_key[i]]

    userLoyalty.save()
    return JsonResponse({'detail': 'success edit'}, status=status.HTTP_200_OK)


def auth(request):
    token = request.COOKIES.get('jwt')
    
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    
    payload = jwt.decode(token,JWT_KEY,algorithms=['HS256'],options={"verify_exp": False})
    
    payload.pop('exp')
    payload.pop('iat')
    return payload