FROM python:3.14-alpine
WORKDIR /app
RUN pip install --no-cache-dir "httpx>=0.28.1,<1"
COPY src/ .
CMD ["python", "main.py"]
