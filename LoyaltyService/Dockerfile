FROM python:3.9

ENV PYTHONUNBUFFERED 1

WORKDIR /app/LoyaltyService

COPY requirements.txt /app/LoyaltyService/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/LoyaltyService

CMD ["sh", "-c", " /usr/local/bin/python LoyaltyService/manage.py makemigrations && /usr/local/bin/python LoyaltyService/manage.py migrate && /usr/local/bin/python LoyaltyService/manage.py runserver 0.0.0.0:8050"]

