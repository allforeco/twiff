# Docker

All docker images should be called from project root directory. The application requires the Twitter Developer API keys; place the keys in a dev.env file in the job directory e.g. `docker\search\dev.env'.

### Building an image

To build a docker image, from the root directory run the following.

`docker\search\build.sh`

### Running a service

To spin up a docker service, from the root directory run the following.

`docker\search\run.sh`

### Stopping a service

To shutdown a docker service, from the root directory run the following.

`docker\search\stop.sh`
