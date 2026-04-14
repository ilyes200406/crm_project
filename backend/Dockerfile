FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps: psycopg2, lxml/pycairo (xhtml2pdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    libxml2-dev libxslt1-dev \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY insomea_crm/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY insomea_crm/ .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
