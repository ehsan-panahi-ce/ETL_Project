FROM python:3-slim
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2 sqlalchemy \
    && pip install pandas \
    && pip install numpy \
    && pip install geopy \
    && pip install PyMySQL \
    && pip install cryptography

WORKDIR /app
COPY . .
CMD [ "python", "./analytics.py" ]