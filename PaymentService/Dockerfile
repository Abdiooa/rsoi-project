FROM python:3.9
ENV PYTHONUNBUFFERED 1
WORKDIR /app/PaymentService

COPY requirements.txt /app/PaymentService/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/PaymentService

CMD ["sh", "-c", " /usr/local/bin/python PaymentService/manage.py makemigrations && /usr/local/bin/python PaymentService/manage.py migrate && /usr/local/bin/python PaymentService/manage.py runserver 0.0.0.0:8060"]

