# Build backend
FROM python:3.7

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . . 

RUN ["apt-get", "update"]
CMD ["python", "example_db_scripts.py"]
#CMD ["python", "app.py"]
CMD ["gunicorn"  , "-b", "0.0.0.0:5001", "app:app"]
