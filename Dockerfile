FROM python:3.7.2

ADD main.py /

RUN pip install requests==2.26.0 discord.py==1.7.3

CMD [ "python", "./main.py" ]
