FROM python:3.9


ENV PYTHONUNBUFFERED 1

WORKDIR /app/Gatewayservice

COPY requirements.txt /app/Gatewayservice/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/Gatewayservice

CMD ["sh", "-c", " /usr/local/bin/python manage.py makemigrations && /usr/local/bin/python manage.py migrate && /usr/local/bin/python manage.py runserver 0.0.0.0:8080"]
