#!/bin/bash

case "$1" in
  start)
    docker-compose up -d
    ;;
  stop)
    docker-compose down
    ;;
  restart)
    docker-compose down
    docker-compose up 
    ;;
  build)
    docker-compose build
    ;;
  rebuild)
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    ;;
  logs)
    docker-compose logs -f
    ;;
  *)
    echo "Использование:"
    echo "./run.sh start|stop|restart|build|rebuild|logs"
    ;;
esac