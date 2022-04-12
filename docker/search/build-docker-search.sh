#!/bin/bash
docker build -t twiff/search -f ./docker/search/twiff-base.dockerfile --no-cache --build-arg SCRIPTIN="scripts/search/search.sh" .