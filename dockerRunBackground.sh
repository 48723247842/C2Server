#!/bin/bash

sudo docker rm -f "c2-server"

sudo docker run -dit --restart='always' \
--name 'c2-server' \
-p 11001:11001
c2-server