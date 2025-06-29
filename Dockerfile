# Multi-stage build für optimale Image-Größe
FROM python:3.11-slim as builder

# Build-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production Stage
FROM python:3.11-slim

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Non-root User erstellen
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Python-Pakete von Builder-Stage kopieren
COPY --from=builder /root/.local /home/appuser/.local

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Verzeichnisstruktur erstellen
RUN mkdir -p /app/config /app/scripts /app/logs /app/data && \
    chown -R appuser:appuser /app

# Startup-Script kopieren
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh && chown appuser:appuser /app/startup.sh

# Health-Check-Script kopieren
COPY healthcheck.py /app/healthcheck.py
RUN chown appuser:appuser /app/healthcheck.py

# Konfiguration und Scripts kopieren
COPY app/ /app/
RUN chown -R appuser:appuser /app

# User wechseln
USER appuser

# PATH für Python-Pakete erweitern
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Volumes definieren
VOLUME ["/app/config", "/app/scripts", "/app/logs", "/app/data"]

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py

# Startup-Script ausführen
CMD ["/app/startup.sh"]