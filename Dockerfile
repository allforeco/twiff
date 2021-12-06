FROM python:3.9.4
COPY requirements.txt .

RUN pip install -r ./requirements.txt

VOLUME ["/app"]
COPY ./src /app
WORKDIR /app

ENTRYPOINT [ "python", "./search.py" ]