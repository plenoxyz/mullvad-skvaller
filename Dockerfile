FROM --platform=linux/amd64 python:3.11-slim-bullseye

COPY . /app
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

CMD ["python3", "bot.py"]
