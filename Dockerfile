FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update \
    && apt-get -y install libpq-dev gcc
    
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/


COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "RITengine.asgi:application"]