FROM python:3.11-slim

WORKDIR /frontend

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements/frontend.txt .
RUN pip install --no-cache-dir -r frontend.txt

# Copier le code
COPY frontend/ .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address", "0.0.0.0"]
