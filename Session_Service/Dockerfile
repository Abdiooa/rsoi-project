FROM python:3.9


ENV PYTHONUNBUFFERED 1

WORKDIR /app/Session_Service

COPY requirements.txt /app/Session_Service/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/Session_Service


CMD ["sh", "-c", "/usr/local/bin/python manage.py makemigrations && /usr/local/bin/python manage.py migrate && /usr/local/bin/python manage.py create_default_admin && /usr/local/bin/python manage.py runserver 0.0.0.0:8040"]
