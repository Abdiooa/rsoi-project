FROM python:3.9

ENV PYTHONUNBUFFERED 1

WORKDIR /app/Session_Service

COPY requirements.txt /app/Session_Service/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/Session_Service

RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py create_default_admin

CMD ["python", "manage.py", "runserver", "0.0.0.0:8040"]
