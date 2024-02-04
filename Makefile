activate:
	CALL conda.bat activate Binance-Futures-Bot

pull-base:
	docker pull spshan/bot-base

pull-binance-bot:
	docker pull spshan/bot-backend

build-base:
	docker build ./base_docker_image/. -t bot-base

push-base:
	docker tag bot-base spshan/bot-base && docker push spshan/bot-base

build:
	docker build . -t spshan/bot-backend

push-backend:
	docker push spshan/bot-backend

run:
	docker run --rm --name bot-backend-instance -p 5000:5000 --env-file test.env -d spshan/bot-backend

kill:
	docker rm bot-backend-instance -f

run-it:
	docker run --rm --name bot-backend-instance -p 5000:5000 --env-file test.env -it spshan/bot-backend /bin/bash

list:
	docker ps -a
