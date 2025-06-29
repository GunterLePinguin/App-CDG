FROM python:3.11-slim

WORKDIR /generator

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements/generator.txt .
RUN pip install --no-cache-dir -r generator.txt

# Copier le code
COPY data_generator/ .

CMD ["python", "main.py"]
