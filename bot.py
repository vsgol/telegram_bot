import argparse
from shutil import rmtree
import os
from os.path import exists

import re
from telegram import (
    ForceReply,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from tweet_capture.exceptions_tc import BasicExceptionTC, WebdriverExceptionTC
from tweet_capture.tweet_capture import TweetCapture
from config import TELEGRAM_BOT_TOKEN
import logging
from logging.handlers import TimedRotatingFileHandler

logger_handler = TimedRotatingFileHandler(
    filename=f"{os.getcwd()}/telegram_bot.log", when="W4"
)
logger_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s — %(name)s — %(levelname)s — %(message)s", datefmt="%d/%m %H:%M:%S"
    )
)
logger = logging.getLogger(__name__)
logger.addHandler(logger_handler)
logger.setLevel(logging.INFO)

class TwitterFrameHandler:
    tweet = TweetCapture()
    tweet.set_wait_time(15)
    
    
    # Parser settings
    class __TweetLinkType:
            def __init__(self, link):
                m = re.match(
                    "^https?:\/\/(twitter\.com|x\.com)\/(?P<user_name>\w+)\/status(es)?\/(?P<tweet_id>\d+)(\S*)?",
                    link,
                )
                if m is None:
                    raise argparse.ArgumentTypeError("Invalid link")
                self.url = f"https://twitter.com/{m.group('user_name')}/status/{m.group('tweet_id')}"
                self.user_name = m.group("user_name")
                self.id = m.group("tweet_id")

    parser = argparse.ArgumentParser(prog='', exit_on_error=False)
    parser.add_argument("twitter_link", type=__TweetLinkType)
    parser.add_argument(
        "--mode",
        default=2,
        type=int,
        help="Display mode for tweet (0-4)",
        nargs="?",
    )
    parser.add_argument(
        "--night",
        default=1,
        type=int,
        help="Display night mode for tweet (0-2)",
        nargs="?",
    )
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument(
        "-m", "--media-only", help="Save media only", action="store_true"
    )
    command_group.add_argument(
        "-s", "--screenshot-only", help="Save only screenshot", action="store_true"
    )

    async def twitter_link_handler(self, update: Update, context):
        logger.info(
            f"Message from {update.message.author_signature} with message {update.message.text}"
        )
        user_message = update.message.text
        try:
            args = self.parser.parse_args(user_message.split())
        except argparse.ArgumentError as err:
            logger.error(
                f"User entered the wrong arguments, message={user_message}", exc_info=True
            )
            await update.message.reply_text(
                text=f"Failed to parse command.\nUnrecognized arguments: {err}\n{self.parser.format_usage()}", 
                reply_to_message_id=update.message.message_id,
            )
            return

        tweet = args.twitter_link
        screenshot_path = f"screenshots-{tweet.id}"
        media_path = f"{screenshot_path}/media"

        if not exists(screenshot_path):
            os.makedirs(screenshot_path)
        if not exists(media_path):
            os.makedirs(media_path)

        logger.info(f"Started processing {tweet.url}")

        try:
            info = await self.tweet.capture(
                tweet.url,
                screenshot_path,
                media_path,
                mode=args.mode,
                night_mode=args.night,
                only_screenshot=args.screenshot_only,
                only_media=args.media_only,
            )
            logger.info(f"Started sending answer to {update.message.author_signature}")

            if args.screenshot_only:
                caption = f"Screenshot of {tweet.url}"
            elif args.media_only:
                caption = f"Media of {tweet.url}"
            else:
                caption = f"Tweet {tweet.url}"
                
            if "TB" in info:
                caption = (
                    "WARNING, the tweet contains the opinion of twitter blue user\n\n"
                    + caption
                )

            media_group = []
            for root, _, files in os.walk(screenshot_path):
                for media in files:
                    if media.endswith(".png"):
                        media_group.append(
                            InputMediaPhoto(
                                open(os.path.join(root, media), "rb"),
                                has_spoiler="TB" in info,
                            )
                        )
                    elif media.endswith(".mp4"):
                        media_group.append(
                            InputMediaVideo(
                                open(os.path.join(root, media), "rb"),
                                has_spoiler="TB" in info,
                            )
                        )

            # Send the screenshot to the Telegram channel
            await update.message.reply_media_group(
                media=media_group,
                caption=caption,
                reply_to_message_id=update.message.message_id,
            )
        except BasicExceptionTC as err:
            logger.error(
                f"Failed to process tweet, message = {user_message}", exc_info=True
            )
            await update.message.reply_text(
                text=f"Failed to process tweet: {err}",
                reply_to_message_id=update.message.message_id,
            )
            return

        logger.info(f"Finished with {update.message.author_signature}")
        # Clean up: delete the screenshot file
        rmtree(media_path)
        rmtree(screenshot_path)

    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text(self.parser.format_help())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

def main() -> None:
    default_handler = TwitterFrameHandler()

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", default_handler.help_command))
    
    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, default_handler.twitter_link_handler
        )
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
