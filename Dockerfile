FROM python:3.11-slim

# Installing minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget unzip jq git ca-certificates \
    libglib2.0-0 libnss3 libx11-6 libxss1 libasound2 \
    libatk-bridge2.0-0 libgtk-3-0 libdrm2 libgbm1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Latest stable version of Chrome and ChromeDriver
RUN export CHROME_JSON=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json) && \
    export VERSION=$(echo $CHROME_JSON | jq -r '.channels.Stable.version') && \
    export CHROME_URL=$(echo $CHROME_JSON | jq -r ".channels.Stable.downloads.chrome[] | select(.platform == \"linux64\") | .url") && \
    export DRIVER_URL=$(echo $CHROME_JSON | jq -r ".channels.Stable.downloads.chromedriver[] | select(.platform == \"linux64\") | .url") && \
    curl -o chrome.zip $CHROME_URL && \
    curl -o chromedriver.zip $DRIVER_URL && \
    unzip chrome.zip && \
    unzip chromedriver.zip && \
    mv chrome-linux64 /opt/chrome && \
    ln -sf /opt/chrome/chrome /usr/local/bin/chrome && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf chrome.zip chromedriver.zip chrome-linux64 chromedriver-linux64


# Cloning Telegram bot
WORKDIR /app
RUN git clone https://github.com/vsgol/telegram_bot.git .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Running bot
CMD ["python3", "bot.py"]
