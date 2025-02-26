FROM python:3.9-slim

# Create app user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy files and set ownership to app user
COPY --chown=app:app . .

# Switch to app user
USER app

CMD ["python", "app.py"]