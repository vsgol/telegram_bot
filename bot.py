import argparse
from shutil import rmtree
import os
from os.path import exists
import asyncio

import re
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from tweet_capture import TweetCapture, BasicExceptionTC, get_logger
from config import TELEGRAM_BOT_TOKEN, AUTHOR_ID

logger = get_logger(__name__)

class TwitterFrameHandler:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.close()
        # Clean up: delete the screenshots files
        for dir in os.listdir():
            if dir.startswith('screenshots-'):
                rmtree(dir)
        self.tweet.quit()

    tweet = TweetCapture()

    # Parser settings
    class __TweetLinkType:
        def __init__(self, link):
            m = re.match(
                "^(https?:\/\/)?(www\.)?(twitter\.com|x\.com)\/(?P<user_name>\w+)\/status(es)?\/(?P<tweet_id>\d+)(\S*)?",
                link,
            )
            if m is None:
                raise argparse.ArgumentTypeError("Invalid link")
            self.url = f"https://twitter.com/{m['user_name']}/status/{m['tweet_id']}"
            self.user_name = m["user_name"]
            self.id = m["tweet_id"]

    parser = argparse.ArgumentParser(prog="", exit_on_error=False)
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

    async def __download_tweet(self, update: Update, context: ContextTypes.DEFAULT_TYPE, args, control_message_id):
        tweet = args.twitter_link
        screenshot_path = f"screenshots-{tweet.id}"
        media_path = f"{screenshot_path}/media"
        context.user_data[control_message_id]["screenshot_path"] = screenshot_path
        context.user_data[control_message_id]["tweet_url"] = tweet.url

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
                only_screenshot=context.user_data[control_message_id]["choices"]["screenshot"],
                only_media=context.user_data[control_message_id]["choices"]["media"],
            )
            context.user_data[control_message_id]["tweet_info"] = info
            logger.info(f"Started sending answer to {update.effective_user.name}")

            # Send the media group (photos/videos)
            await send_media_message(update, context, control_message_id=control_message_id)

            # Schedule the deletion of the control message and media after 1 hour
            asyncio.create_task(delete_media_after_delay(context, control_message_id=control_message_id))
            try:
                await context.bot.edit_message_text(
                    chat_id=context.user_data[control_message_id]['chat_id'],
                    message_id=control_message_id,
                    text="Tweet processed. You can modify your selection:",
                    reply_markup=InlineKeyboardMarkup(build_keyboard(
                            context, 
                            context.user_data[control_message_id]["choices"]
                        ))
                )
            except Exception as e:
                logger.error(f"Failed to update control message: {e}")

        except BasicExceptionTC as err:
            logger.error(
                f"Failed to process tweet, message = {tweet.url}", exc_info=True
            )
            await update.message.reply_text(
                text=f"Failed to process tweet: {err}",
                reply_to_message_id=update.message.message_id,
            )
            return
        logger.info(f"Finished with {update.effective_user.name}")

    async def twitter_link_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(
            f"Message from {update.effective_user.name} with message {update.message.text}"
        )
        user_message = update.message.text
        try:
            args, argv = self.parser.parse_known_args(user_message.split())
            if argv:
                raise argparse.ArgumentError(None, f"Unrecognized arguments: {argv}")
        except argparse.ArgumentError as err:
            logger.error(
                f"User entered the wrong arguments, message={user_message}", exc_info=True
            )
            await update.message.reply_text(
                text=f"Failed to parse command.\nUnrecognized arguments: {err}\n{self.parser.format_usage()}",
                reply_to_message_id=update.message.message_id,
            )
            return

        choices = {"screenshot": args.screenshot_only, "media": args.media_only, "censor": False}
        # Inform the user that processing has started
        control_message = await update.message.reply_text(
            text="Processing your tweet...",
            reply_markup=InlineKeyboardMarkup(build_keyboard(context, choices))
        )
        control_message_id = control_message.message_id
        context.user_data[control_message_id] = {
            "user_message_id": update.message.message_id,
            "chat_id": update.message.chat_id,
            "choices": choices
        }

        asyncio.create_task(self.__download_tweet(update, context, args, control_message_id))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text(self.parser.format_help())


async def delete_media_after_delay(context: ContextTypes.DEFAULT_TYPE, control_message_id):
    await asyncio.sleep(3600)  # Wait for 1 hour (3600 seconds)
    # Delete the control message
    user_data = context.user_data[control_message_id]
    try:
        await context.bot.delete_message(
            chat_id=user_data["chat_id"],
            message_id=control_message_id
        )
        rmtree(user_data["screenshot_path"])
        context.user_data.pop(control_message_id, None)
    except Exception as e:
        logger.error(f"Failed to delete control message: {e}")


async def send_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE, control_message_id):
    user_data = context.user_data.get(control_message_id)
    if (user_data is None or "tweet_info" not in user_data):
        return

    tweet_url = user_data["tweet_url"]

    choices = user_data["choices"]
    if choices["screenshot"]:
        caption = f"Screenshot of {tweet_url}"
    elif choices["media"]:
        caption = f"Media of {tweet_url}"
    else:
        caption = f"Tweet {tweet_url}"

    if "TB" in user_data["tweet_info"]:
        caption = (
            "WARNING, the tweet contains the opinion of a Twitter Blue user\n\n"
            + caption
        )

    media_group = []
    root = user_data["screenshot_path"]
    if (not choices["media"]):
        media_group.append(
            InputMediaPhoto(
                open(os.path.join(root, "screenshot.png"), "rb"),
                has_spoiler=choices["censor"],
            )
        )
    if (not choices["screenshot"]):
        path = os.path.join(root, "media")
        for file in os.listdir(path):
            if file.endswith(".png"):
                media_group.append(
                    InputMediaPhoto(
                        open(os.path.join(path, file), "rb"),
                        has_spoiler=choices["censor"],
                    )
                )
            elif file.endswith(".mp4") or file.endswith(".gif"):
                media_group.append(
                    InputMediaVideo(
                        open(os.path.join(path, file), "rb"),
                        has_spoiler=choices["censor"],
                    )
                )

    if "media_message_ids" in user_data:
        try:
            for message_id in user_data["media_message_ids"]:
                await context.bot.delete_message(
                    chat_id=user_data["chat_id"],
                    message_id=message_id
                )
        except Exception as e:
            logger.error(f"Failed to delete media message: {e}")
            return

    try:
        media_messages = await context.bot.send_media_group(
            chat_id=user_data["chat_id"],
            media=media_group,
            caption=caption,
            reply_to_message_id=user_data["user_message_id"]
        )
        user_data["media_message_ids"] = [m.message_id for m in media_messages]
    except Exception as e:
        logger.error(f"Failed to update message: {e}")


def build_keyboard(context: ContextTypes.DEFAULT_TYPE, choices):    
    return [
        [
            InlineKeyboardButton(
                f"Only Screenshot {'✅' if choices['screenshot'] else ''}",
                callback_data="screenshot",
            ),
            InlineKeyboardButton(
                f"Only Media {'✅' if choices['media'] else ''}",
                callback_data="media",
            ),
        ],
        [
            InlineKeyboardButton(
                f"Censor Image {'✅' if choices['censor'] else ''}",
                callback_data="censor",
            )
        ],
    ]


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    control_message_id = update.callback_query.message.message_id
    user_data = context.user_data.get(control_message_id)

    choice = query.data
    choices = user_data["choices"]

    if choice == "censor":
        choices["censor"] = not choices["censor"]
    elif choice == "media":
        choices["media"] = not choices["media"]
        if choices["media"]:
            choices["screenshot"] = False  # Deselect screenshot if media is selected
    elif choice == "screenshot":
        choices["screenshot"] = not choices["screenshot"]
        if choices["screenshot"]:
            choices["media"] = False  # Deselect media if screenshot is selected
    context.user_data[control_message_id]["choices"] = choices

    # Update the buttons in the existing message
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=user_data["chat_id"],
            message_id=control_message_id,
            reply_markup=InlineKeyboardMarkup(build_keyboard(context, choices))
        )
    except Exception as e:
        print(f"Error updating buttons: {e}")

    # Update the message with the current choices
    await send_media_message(update, context, control_message_id=control_message_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(rf"Hi {user.mention_html()}!")

# Add flags for more options
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send logs to me"""
    if update.effective_user.id != AUTHOR_ID:
        await update.message.reply_text("Sorry you don't have permissions to see this.")
        return
    await update.message.reply_document(document="telegram_bot.log")
    return


def main():
    with TwitterFrameHandler() as default_handler:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("logs", logs))
        application.add_handler(CommandHandler("help", default_handler.help_command))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, default_handler.twitter_link_handler
            )
        )

        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
