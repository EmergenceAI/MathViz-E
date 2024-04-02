#!/bin/bash -xe

docker build -t my_desmos .
docker run -p 5001:5001 my_desmos