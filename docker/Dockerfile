FROM python:3.14-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x docker/entrypoint.sh
ENTRYPOINT ["/app/docker/entrypoint.sh"]

FROM base AS dev
CMD ["fastapi", "dev", "--host", "0.0.0.0"]

FROM base AS prod
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
