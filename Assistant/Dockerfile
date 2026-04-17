FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8500

EXPOSE 8500

CMD ["sh", "-c", "uvicorn assistant:app --host 0.0.0.0 --port ${PORT:-8500}"]

