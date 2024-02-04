FROM spshan/bot-base

WORKDIR /app
COPY . .

ENV PYTHONPATH /app
ENV FLASK_APP /app/run.py

#RUN flask shell
#RUN from binance_bot import db && db.create_all() && exit()


ENTRYPOINT ["python"]
CMD ["run.py"]