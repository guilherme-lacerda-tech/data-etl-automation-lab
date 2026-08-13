FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY data/sample ./data/sample
COPY examples ./examples

RUN pip install --no-cache-dir .

CMD ["python", "examples/run_demo.py"]
