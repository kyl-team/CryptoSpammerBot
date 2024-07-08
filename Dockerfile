FROM python:3.12.4

WORKDIR /usr/app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/app
COPY ./src src
ENV PYTHONPATH=/usr/app/src

CMD [ "python", "src/main.py" ]
