FROM python:3.9


ENV PYTHONUNBUFFERED 1

WORKDIR /app/ReservationService

COPY requirements.txt /app/ReservationService/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/ReservationService


CMD ["sh", "-c", "/usr/local/bin/python ReservationService/manage.py makemigrations && /usr/local/bin/python ReservationService/manage.py migrate && /usr/local/bin/python ReservationService/manage.py runserver 0.0.0.0:8070"]