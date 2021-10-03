import logging
import os
from io import BytesIO
import datetime

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, JobQueue
from make_grid import make_grid, rows as grid_rows, cols as grid_cols
from hash_image import filename_to_hash, hash_is_astolfo

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def on_join(update: Update, context: CallbackContext):
    print(update.message.new_chat_members)
    user = update.message.new_chat_members[0]
    if user.is_bot:
        return
    bio = BytesIO()
    bio.name = 'image.jpeg'
    grid_img, grid_tiles = make_grid()
    grid_img.save(bio, 'JPEG')
    bio.seek(0)
    markup = [[]*grid_cols for _ in range(grid_rows)]
    for row in range(grid_rows):
        for col in range(grid_cols):
            img_hash = filename_to_hash[grid_tiles.pop(0)]
            markup[row].append([])
            markup[row][col] = InlineKeyboardButton(callback_data=img_hash, text=grid_rows+grid_cols-len(grid_tiles))
    msg = context.bot.send_photo(
        caption=f"Welcome to the group, {user.first_name}! "
                f"To prove you aren't a bot, please select the image that contains Astolfo",
        reply_markup=InlineKeyboardMarkup(markup),
        photo=bio,
        chat_id=update.message.chat_id,
        reply_to_message_id=update.message.message_id)
    context.job_queue.run_once(callback_timeout, 60, context=msg, name=str(update.message.message_id))


def callback_timeout(context: CallbackContext) -> None:
    print(context.job.context.chat_id)
    context.job.context.delete()
    context.bot.send_message(text='Captcha timeout - user has been kicked', chat_id=context.job.context.chat_id, reply_to_message_id=context.job.context.reply_to_message.message_id)
    try:
        context.bot.ban_chat_member(
            chat_id=context.job.context.chat_id,
            user_id=context.job.context.reply_to_message.new_chat_members[0].id,
            until_date=datetime.datetime.now() + datetime.timedelta(minutes=1)
        )
    except telegram.error.BadRequest:
        context.bot.send_message(text='I was unable to kick user - double check I have admin permissions?', chat_id=context.job.context.chat_id)


def handle_correct(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.delete_message()
    context.bot.send_message(text='Thank you for completing the captcha, enjoy your stay!~', chat_id=query.message.chat_id, reply_to_message_id=query.message.reply_to_message.message_id)

def handle_incorrect(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.delete_message()
    context.bot.send_message(text='Captcha failed - user has been kicked', chat_id=query.message.chat_id, reply_to_message_id=query.message.reply_to_message.message_id)
    try:
        context.bot.ban_chat_member(
            chat_id=query.message.chat_id,
            user_id=query.message.reply_to_message.new_chat_members[0].id,
            until_date=datetime.datetime.now() + datetime.timedelta(minutes=1)
        )
    except telegram.error.BadRequest:
        context.bot.send_message(text='ERROR: No admin permissions, unable to kick user', chat_id=query.message.chat_id)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.from_user.id != query.message.reply_to_message.new_chat_members[0].id:
        return
    context.job_queue.get_jobs_by_name(str(query.message.reply_to_message.message_id))[0].schedule_removal()
    correct = hash_is_astolfo[query.data]
    if correct:
        handle_correct(update, context)
    else:
        handle_incorrect(update, context)


def main():
    updater = Updater(os.getenv('API_KEY'), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, on_join, pass_job_queue=True))
    dp.add_handler(CallbackQueryHandler(button, pass_job_queue=True))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()