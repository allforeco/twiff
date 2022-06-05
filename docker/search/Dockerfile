#syntax = docker/dockerfile:1.2

FROM python:3.9.7

# Move src files
COPY ./src/ /app/

# Move configuration files
RUN mkdir /app/config
COPY scripts/search/*.json /app/config/

# Create Volumes
RUN mkdir /app/output
RUN mkdir /app/logs

# Install Requirements
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Mount Secrets
RUN --mount=type=secret,id=twitter-dev,target=/run/secrets/dev.env cat /run/secrets/dev.env

# Run Script
ARG SCRIPTIN
COPY $SCRIPTIN /app/search.sh
CMD ["/app/search.sh"]