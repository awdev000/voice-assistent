FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# 1. Системные зависимости (редко меняются)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nano \
    portaudio19-dev \
    libsndfile1 \
    build-essential \
    curl \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# 2. Сначала копируем requirements (чтобы кешировалось)
COPY requirements.txt .

# 3. Устанавливаем зависимости (это самый долгий слой)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# 4. НЕ копируем код сюда
# Код будет монтироваться через volume
# Установка Piper для ARM64 (Raspberry Pi)
RUN curl -L https://github.com/rhasspy/piper/releases/latest/download/piper_linux_aarch64.tar.gz \
    -o /tmp/piper.tar.gz && \
    mkdir -p /opt/piper && \
    tar -xzf /tmp/piper.tar.gz -C /opt/piper && \
    find /opt/piper -type f -name "piper" -exec chmod +x {} \; && \
    ln -s $(find /opt/piper -type f -name "piper") /usr/local/bin/piper && \
    rm /tmp/piper.tar.gz

CMD ["watchmedo", "auto-restart", "--directory=.", "--pattern=*.py", "--recursive", "--", "python", "main.py"]