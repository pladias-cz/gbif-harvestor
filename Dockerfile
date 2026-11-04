FROM python:3.14-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY gbif_harvestor ./gbif_harvestor

USER nobody

ENTRYPOINT ["python", "-m", "gbif_harvestor"]
