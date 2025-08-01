FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ../db_create.py /app/
COPY ../db_import.py /app/

COPY app.py /app/
COPY templates/ /app/templates/

COPY ../veri/ /app/veri/

EXPOSE 80

CMD ["python", "app.py"]
