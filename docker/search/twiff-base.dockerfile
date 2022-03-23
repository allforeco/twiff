FROM python:3.9.4

COPY ./src/ /app/
COPY scripts/search/*.json /app/
COPY requirements.txt ./requirements.txt

ARG SCRIPTIN

COPY $SCRIPTIN /app/run-job.sh
RUN pip install -r requirements.txt
CMD ["/app/run-job.sh"]