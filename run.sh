#!/bin/bash

IMAGE=pik-monitor
TAG=0.1

docker stop $IMAGE
docker rm $IMAGE

docker image rm $IMAGE:$TAG
docker build -t $IMAGE:$TAG .

docker run -d -it\
        -v $PWD/data:/app/data\
        -e PYTHONUNBUFFERED=0\
        -e TZ=Europe/Moscow\
        -e TLG_TOKEN=YOUR_TOKEN\
        -e TLG_CHAT_ID=YOUR_CHAT_ID\
        -e PIK_LOGIN=YOUR_PIK_LOGIN\
        -e PIK_PASSWORD=YOUR_PIK_PASSWORD\
        -e MODE=single\
        -e DELAY=600\
        --name $IMAGE\
        --restart always\
        $IMAGE:$TAG