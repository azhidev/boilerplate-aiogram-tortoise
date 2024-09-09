from aiogram.types import BotCommand, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from aiogram import Bot, Dispatcher, types
from middlewares import LoggingMiddleware
from database import init_db, close_db
from aiogram.enums import ParseMode
from aiogram.filters import Command
from config import BOT_TOKEN
from models import User
import logging, os, asyncio
from functools import wraps


RUNNIG_MODE = os.getenv("RUNNING_MODE", "prod")


logging.basicConfig(level=logging.DEBUG if RUNNIG_MODE == "dev" else logging.INFO)
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)
dp.update.middleware(LoggingMiddleware())
user_auth_cache = {}


async def authenticate_user(message:types.Message):
    if message.chat.id in user_auth_cache:
        if user_auth_cache[message.chat.id]:
            return user_auth_cache[message.chat.id]  
    
    user_exists = await user_exist(message.chat.id)
    
    user_auth_cache[message.chat.id] = user_exists
    return user_exists


def authenticated_only(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        
        authenticate = await authenticate_user(message)
        if authenticate:
            return await func(message, *args, **kwargs)
        else:
            await show_phone_number_request(message, "لطفا شماره تلفن خود را از طریق منو زیر به اشتراک بگذارید.")
            return
    return wrapper


async def user_exist(user_id):
    return await User.get_or_none(user_id=user_id)


async def phone_number_exist(phone_number):
    print(phone_number)
    return await User.get_or_none(phone_number=phone_number)


async def register_user_to_db(user:User, user_id):
    user.user_id = user_id
    await user.save()
    return user

async def show_phone_number_request(message: types.Message, response):
    phone_button = KeyboardButton(text="اشتراک شماره تلفن", request_contact=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[phone_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply(response, reply_markup=keyboard)

async def show_main_menu(message: types.Message, response):
    tweet_button = KeyboardButton(text="توئیت جدید")
    bot_help_handler = KeyboardButton(text="راهنمای استفاده از بات")
    label_help_handler = KeyboardButton(text="راهنمای برچسب گذاری")
    history_button = KeyboardButton(text="عملکرد گذشته")
    
    main_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[[tweet_button], [bot_help_handler, label_help_handler, history_button]],
        resize_keyboard=True 
    )
    
    await message.reply(response, reply_markup=main_menu_keyboard)


async def start_command_handler(message: types.Message):
    user = await user_exist(message.chat.id)
    
    if user:
        await show_main_menu(message, "شما وارد شده اید!")  
    else:
        await show_phone_number_request(message, "لطفا شماره تلفن خود را از طریق منو زیر به اشتراک بگذارید.")


async def contact_handler(message: types.Message):
    if message.contact:
        if message.contact.user_id == message.from_user.id:
            user = await phone_number_exist(message.contact.phone_number)
            if user:
                await register_user_to_db(user, message.chat.id)
                await show_main_menu(message, "ورود شما موفقیت آمیز بود!")  
            else:
                await message.reply("شما دسترسی مجاز به این بات را ندارید!")
        else:
            await message.reply("لطفا شماره تلفن خود را از طریق منو به اشتراک بگذارید.")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="شروع"),
    ]
    await bot.set_my_commands(commands)

@authenticated_only
async def tweet_handler(message: types.Message):
    await message.reply("This is your tweet.")


async def bot_help_handler(message: types.Message):
    await message.reply("Here are your bot help.")


async def label_help_handler(message: types.Message):
    await message.reply("Here are your label help.")


async def history_handler(message: types.Message):
    await message.reply("Here are your history help.")


async def main():
    await init_db()

    dp.message.register(start_command_handler, Command(commands=["start"]))
    # dp.callback_query.register(phone_number_request_callback_handler, lambda callback_query: callback_query.data == "share_phone")
    

    dp.message.register(tweet_handler, lambda message: message.text == "توئیت جدید")
    dp.message.register(bot_help_handler, lambda message: message.text == "راهنمای استفاده از بات")
    dp.message.register(history_handler, lambda message: message.text == "عملکرد گذشته")
    dp.message.register(label_help_handler, lambda message: message.text == "راهنمای برچسب گذاری")
    dp.message.register(contact_handler, lambda message: message.contact)

    # dp.message.register(save_message_handler)
    await set_bot_commands(bot)
    
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
