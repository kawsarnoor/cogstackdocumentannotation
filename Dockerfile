# Build backend
FROM python:3.7

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . . 

RUN ["apt-get", "update"]
WORKDIR /api

CMD ["gunicorn"  , "-b", "0.0.0.0:5001", "-w", "2", "run:app"]
