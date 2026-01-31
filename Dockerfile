FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src
COPY web /app/web
COPY README.md /app/README.md
COPY .env.example /app/.env.example

RUN pip install --no-cache-dir .

EXPOSE 9470

CMD ["uvicorn", "photo_pacs.main:app", "--host", "0.0.0.0", "--port", "9470"]
