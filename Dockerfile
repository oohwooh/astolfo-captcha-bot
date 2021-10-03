from python:3.9-slim-buster

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY bot.py /
COPY config.py /
COPY hash_image.py /
COPY make_grid.py /
COPY OpenSans-Bold.ttf /
COPY images/ /images

CMD ["python3", "bot.py"]