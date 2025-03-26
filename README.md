# Telegram Twitter Screenshot Bot

A Telegram bot that takes a tweet URL and sends back a clean screenshot of the tweet along with all attached media (images, GIFs, videos). This makes it easy to view and share tweet content directly inside Telegram — without opening a browser or dealing with regional blocks.

## Features

- 📸 Tweet screenshots rendered in a real browser
- 🎞 Media download (images, GIFs, videos)
- ⚙️ Optional settings: censorship, format selection, etc.
- 🔗 Original tweet link included in every response
- 🧪 Dockerized for easy deployment

## Requirements

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

No need to install Python, Chrome, or Chromedriver — everything runs inside a container.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/vsgol/telegram_bot.git
cd telegram_bot
```

### 2. Configure environment variables

Create a `.env` file in the root of the project with the following content:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_BOT_AUTHOR=your_numeric_telegram_id
```

- `TELEGRAM_BOT_TOKEN` — your bot's token from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_BOT_AUTHOR` — your personal Telegram numeric ID (used to access bot logs via commands)

You can find your ID using [@userinfobot](https://t.me/userinfobot) on Telegram.

### 3. Run the bot

Make sure Docker is installed and running, then use the provided script:

```bash
./run_bot.sh
```

This script will:
- Build the Docker image
- Start the container in detached mode

To stop the bot:

```bash
docker-compose down
```

## Known Limitations

- Only one browser instance at a time (due to low ram on my server)
- Twitter's layout changes often — sometimes breaks screenshot cleaning

## License

MIT License
