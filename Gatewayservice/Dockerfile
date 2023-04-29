FROM python:3.9


ENV PYTHONUNBUFFERED 1

WORKDIR /app/Gatewayservice

COPY requirements.txt /app/Gatewayservice/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/Gatewayservice

CMD ["sh", "-c", " /usr/local/bin/python Gatewayservice/manage.py makemigrations && /usr/local/bin/python Gatewayservice/manage.py migrate && /usr/local/bin/python Gatewayservice/manage.py runserver 0.0.0.0:8090"]
