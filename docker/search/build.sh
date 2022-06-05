#!/bin/bash
docker swarm init
docker build -t twiff/search -f ./docker/search/Dockerfile --secret id=twitter-dev,src=./docker/search/dev.env --build-arg SCRIPTIN="scripts/search/search.sh" --progress=plain .