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


RUNNIG_MODE = os.getenv("RUNNING_MODE", "prod")


logging.basicConfig(level=logging.DEBUG if RUNNIG_MODE == "dev" else logging.INFO)
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)
dp.update.middleware(LoggingMiddleware())


async def user_exist(user_id):
    return await User.get_or_none(user_id=user_id)


async def phone_number_exist(phone_number):
    print(phone_number)
    return await User.get_or_none(phone_number=phone_number)


async def register_user_to_db(user:User, user_id):
    user.user_id = user_id
    await user.save()
    return user


async def show_main_menu(message: types.Message, response):
    profile_button = KeyboardButton(text="Profile")
    orders_button = KeyboardButton(text="Orders")
    logout_button = KeyboardButton(text="Logout")
    
    main_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[[profile_button], [orders_button], [logout_button]],
        resize_keyboard=True 
    )
    
    await message.reply(response, reply_markup=main_menu_keyboard)


async def start_command_handler(message: types.Message):
    user = await user_exist(message.chat.id)
    
    if user:
        await show_main_menu(message, "You are already registered.")  
    else:
        phone_button = KeyboardButton(text="Share your phone number", request_contact=True)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[phone_button]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.reply("Please share your phone number by clicking the button in menu.", reply_markup=keyboard)


async def contact_handler(message: types.Message):
    if message.contact:
        if message.contact.user_id == message.from_user.id:
            user = await phone_number_exist(message.contact.phone_number)
            if user:
                await register_user_to_db(user, message.chat.id)
                await show_main_menu(message, "You have been successfully registered!")  
            else:
                await message.reply("You do not have access to this bot.")
        else:
            await message.reply("this is not your phone number")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
    ]
    await bot.set_my_commands(commands)


async def profile_handler(message: types.Message):
    await message.reply("This is your profile.")


async def orders_handler(message: types.Message):
    await message.reply("Here are your orders.")


async def logout_handler(message: types.Message):
    await message.reply("You have logged out.")


async def main():
    await init_db()

    dp.message.register(start_command_handler, Command(commands=["start"]))
    # dp.callback_query.register(phone_number_request_callback_handler, lambda callback_query: callback_query.data == "share_phone")
    

    dp.message.register(profile_handler, lambda message: message.text == "Profile")
    dp.message.register(orders_handler, lambda message: message.text == "Orders")
    dp.message.register(logout_handler, lambda message: message.text == "Logout")
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
