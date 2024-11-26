# Immagine base python
FROM python:3.9-slim

WORKDIR /app

# Installa i pacchetti richiesti
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Subfinder
RUN wget https://github.com/projectdiscovery/subfinder/releases/download/v2.5.7/subfinder_2.5.7_linux_amd64.zip \
    && unzip subfinder_2.5.7_linux_amd64.zip \
    && mv subfinder /usr/local/bin/ \
    && rm subfinder_2.5.7_linux_amd64.zip

# Nuclei
RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v2.9.6/nuclei_2.9.6_linux_amd64.zip \
    && unzip nuclei_2.9.6_linux_amd64.zip \
    && mv nuclei /usr/local/bin/ \
    && rm nuclei_2.9.6_linux_amd64.zip

# Template di Nuclei e update Subfinder
RUN nuclei -update-templates
RUN subfinder -up

# Copia i file di progetto nel container
COPY requirements.txt requirements.txt
COPY subdomain_takeover_docker.py subdomain_takeover_docker.py
COPY provider-config.yaml /root/.config/subfinder/provider-config.yaml

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Volume per i file di input/output
VOLUME ["/app/data"]

CMD ["python", "subdomain_takeover_docker.py"]
