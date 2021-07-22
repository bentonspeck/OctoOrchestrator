#!/bin/bash
app="docker.test"
docker build -t ${app} .
#docker run -d -p 56733:8080 \
winpty docker run -it --rm -p 56733:80 \
  --name="docker.test" \
  -v $PWD:/app "docker.test"