import logging

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from utils import AdminState
from config import TOKEN, BLACKLIST, CHARS
from messages import MESSAGES
import json

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())

usr = None
tokens_fee = 0.1


class User:

    def __init__(self, _id: int):
        with open('data/users.json', 'r') as fp:
            usrs = json.load(fp)
        if str(_id) in usrs:
            self.is_admin = usrs[str(_id)]["is_admin"]
            self.tokens = usrs[str(_id)]["tokens"]
            self.rating = usrs[str(_id)]["rating"]
        else:
            self.is_admin = False
            self.tokens = 0
            self.rating = 0
            new_user = {str(_id): {
                'is_admin': self.is_admin,
                'tokens': self.tokens,
                'rating': self.rating,
            }}
            with open('data/users.json', 'w') as fp:
                usrs = usrs | new_user
                json.dump(usrs, fp)

    def get_tokens(self) -> int:
        return self.tokens

    def get_is_admin(self) -> bool:
        return self.is_admin

    def get_rating(self) -> int:
        return self.rating

    def set_tokens(self, plus_tokens: int):
        self.tokens += plus_tokens

    def set_rating(self, plus_rating):
        self.rating += plus_rating

    def update(self, _id: int):
        with open('data/users.json', 'r') as fp:
            usrs = json.load(fp)
        with open('data/users.json', 'w') as fp:
            usrs = usrs | {str(_id): {
                'is_admin': self.is_admin,
                'tokens': self.tokens,
                'rating': self.rating,
            }}
            json.dump(usrs, fp)


def check_user(_id: int):
    global usr
    if usr is None:
        usr = User(_id)
    else:
        usr.update(_id)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(MESSAGES['start'])


@dp.message_handler(content_types=["new_chat_members"])
async def handler_new_member(message: types.Message):
    global usr

    msg = (
        f'Привет, {message.new_chat_members[-1].first_name}, напиши /register, чтобы я добавил тебя в свою базу'
    )
    await message.answer(msg)


@dp.message_handler(commands=['help', 'register'])
async def process_help_command(message: types.Message):
    global usr
    check_user(message.from_user.id)
    print()
    if message.chat.id > 0:
        if usr.get_is_admin():
            await message.reply(MESSAGES['help_a'])

    await message.reply(MESSAGES['help'])


@dp.message_handler(commands=['profile'])
async def process_profile_command(message: types.Message):
    if message.chat.id < 0:
        return await message.reply(f'Это действие возможно только в личных сообщениях')
    global usr
    check_user(message.from_user.id)
    msg = (
        f'name: {message.from_user.first_name} \n'
        f'tokens: {usr.get_tokens()} \n'
        f'rating: {usr.get_rating()}\n'
    )
    if usr.get_is_admin():
        msg += f'А ещё ты админ!'
    await message.reply(msg)


@dp.message_handler(commands=['change_fee'])
async def process_change_fee_command(message: types.Message):
    if message.chat.id < 0:
        return await message.reply(f'Это действие возможно только в личных сообщениях')
    global usr
    check_user(message.from_user.id)
    if not usr.get_is_admin():
        return await message.reply(f'Это действие возможно только администратору')
    state = dp.current_state(user=message.from_user.id)
    await message.reply(f'Введите новое значение для награды за символ. \nСейчас: {tokens_fee}')
    await state.set_state(AdminState.all()[0])


@dp.message_handler(state=AdminState.CHANGE_FEE_STATE)
async def first_test_state_case_met(message: types.Message):
    global tokens_fee
    new_fee = message.text
    if new_fee.isdigit():
        tokens_fee = int(new_fee)
    await message.reply(f'Успешно!. \nТеперь: {tokens_fee}')

    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()


@dp.message_handler(content_types=types.message.ContentType.TEXT)
async def unknown_message(message: types.Message):
    check_user(message.from_user.id)
    txt = message.text.split(' ')
    for word in txt:
        for bl in BLACKLIST:
            if bl in word:
                txt.remove(word)
    txt = str(txt)

    for ch in CHARS:
        txt = txt.replace(ch, '')

    print(len(txt) * tokens_fee)
    global usr
    usr.set_tokens(len(txt) * tokens_fee)





async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
