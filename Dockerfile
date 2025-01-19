FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    libffi-dev \
    && pip install poetry

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-interaction --no-ansi

COPY . .

WORKDIR /app/api

RUN echo "Folder structure after copying files:" && ls -R /app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]
