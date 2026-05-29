FROM python:3.12-slim

RUN addgroup --system dlo && \
    adduser --system --ingroup dlo --home /home/dlo --shell /bin/sh dlo && \
    mkdir -p /home/dlo/.local/share && \
    chown -R dlo:dlo /home/dlo

WORKDIR /app

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "setuptools<70.0.0"

COPY --chown=dlo:dlo app/        ./app/
COPY --chown=dlo:dlo alembic/    ./alembic/
COPY --chown=dlo:dlo alembic.ini .
COPY --chown=dlo:dlo pyproject.toml .

RUN mkdir -p /app/reports && chown dlo:dlo /app/reports

USER dlo

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/dlo

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]