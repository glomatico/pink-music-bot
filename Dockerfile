FROM debian:stable-slim

ARG MP4BOX
ARG MP4DECRYPT
ARG FFMPEG
ARG NM3U8DLRE
ARG AMDECRYPT
ARG DOTENV
ARG APP_REPO="."

RUN apt-get update && apt-get install -y \
    libicu-dev \
    git \
    python3 \
    python3-pip \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --break-system-packages uv

WORKDIR /app

COPY ${MP4BOX} /usr/local/bin/MP4Box
COPY ${MP4DECRYPT} /usr/local/bin/mp4decrypt
COPY ${FFMPEG} /usr/local/bin/ffmpeg
COPY ${NM3U8DLRE} /usr/local/bin/N_m3u8DL-RE
COPY ${AMDECRYPT} /usr/local/bin/amdecrypt
RUN chmod +x /usr/local/bin/MP4Box /usr/local/bin/mp4decrypt /usr/local/bin/ffmpeg /usr/local/bin/N_m3u8DL-RE /usr/local/bin/amdecrypt

COPY ${APP_REPO}/pyproject.toml ${APP_REPO}/uv.lock* ${APP_REPO}/.python-version  ./

RUN uv sync --no-cache

COPY ${APP_REPO}/pink_music_bot ./pink_music_bot

COPY ${DOTENV} .env

ENTRYPOINT ["uv", "run", "python", "-m", "pink_music_bot"]
