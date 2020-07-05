FROM python:3.7-slim

RUN apt update && apt install -y gcc libffi-dev libssl-dev &&\
    pip install --no-cache-dir requests python-telegram-bot flatten_dict &&\
    apt remove -y gcc libffi-dev libssl-dev &&\
    apt -y autoremove

WORKDIR /app
COPY . /app
ENTRYPOINT [ "python" ]
CMD [ "tlg_bot.py" ]