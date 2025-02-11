# Use official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy pyproject.toml and poetry.lock to install dependencies
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the rest of the app
COPY . /app/

# Expose port 8000
EXPOSE 8000

# Run migrations and start the ASGI server
CMD ["sh", "-c", "python manage.py migrate && uvicorn config.asgi:application --host 0.0.0.0 --port 8000"]
