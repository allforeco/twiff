FROM python:3.9.4

COPY . /app

WORKDIR /app

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "./search.py" ]