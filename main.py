from typing import Dict, Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter, BaseFilter, invert_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize, KeyboardButton, reply_keyboard_remove)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.deep_linking import create_start_link, decode_payload

from functools import reduce
import os


from aiogram.types import FSInputFile

# Вместо BOT TOKEN HERE нужно вставить токен вашего бота,
# полученный у @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN')
OTREE_LABELS_PATH = os.getenv('OTREE_LABELS_PATH')
ADMIN_ID = os.getenv('ADMIN_ID')
OTREE_ROOM_URL=os.getenv('OTREE_ROOM_URL')

redis = Redis(host='localhost')

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage = RedisStorage(redis=redis)

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

# # Создаем "базу данных" пользователей
# user_dict = {}

# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем

    participated = State()

def generate_buttons(options):
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
    buttons: list[KeyboardButton] = [KeyboardButton(
        text=f'{i}') for i in options]
    kb_builder.row(*buttons, width=1)
    return kb_builder


import requests  # pip3 install requests
from pprint import pprint


# GET = requests.get
# POST = requests.post

# if using Heroku, change this to https://YOURAPP.herokuapp.com
# SERVER_URL = 'http://localhost:8000'
# REST_KEY = os.getenv('REST_KEY')
MESSAGE_TEXT = 'Привет!'\
            '\nТвой друг/знакомый/коллега пригласил тебя поучаствовать в онлайн эксперименте'\
                              '\nЭксперимент займёт не более 5 минут. Ты сможешь заработать от 150 до 400 рублей'\
                              '\nТы можешь в любой момент прекратить участие в эксперименте.'\
                              '\nЧтобы принять участие перейди по индивидуальной ссылке'
# def call_api(method, *path_parts, **params) -> dict:
#     path_parts = '/'.join(path_parts)
#     url = f'{SERVER_URL}/api/{path_parts}/'
#     resp = method(url, json=params, headers={'otree-rest-key': REST_KEY})
#     if not resp.ok:
#         msg = (
#             f'Request to "{url}" failed '
#             f'with status code {resp.status_code}: {resp.text}'
#         )
#         raise Exception(msg)
#     return resp.json()

@dp.message(CommandStart(),~StateFilter(FSMFillForm.participated))
async def process_start_command(message: Message, state: FSMContext):
    args = message.text.replace('/start ', '')
    if args == "/start":
        await message.answer(text='Войдите в бот по пригласительной ссылке от вашего друга')
    else:
        participants_raw = await redis.keys()
        participants = []
        for i in participants_raw:
            i = str(i)
            print(i[-5:])
            if i[-5:] == "data'":
                a = i.split(":")
                print(a)
                participants.append(a[1])
        reference = decode_payload(args)
        if (reference in participants) or (str(message.from_user.id) == str(ADMIN_ID)):
            amount_of_participated = len(participants)
            with open(f'{OTREE_LABELS_PATH}') as f:
                contents = f.read()
            codes = contents.split(sep="\n")
            part_code = codes[amount_of_participated]
            # send_inviter = call_api(
            #     POST,
            #     'participant_vars',
            #     room_name='behexp',
            #     participant_label=part_code,
            #     vars=dict(inviter=args),
            # )
            # print(send_inviter)
            await message.answer(text=MESSAGE_TEXT)
            await message.answer(text=f'{OTREE_ROOM_URL}?participant_label={part_code}')
            user_id = message.from_user.id
            link_for_other = await create_start_link(bot, user_id, encode=True)
            await state.update_data(data=dict(
                otree_code=part_code,
                referal=reference,
                user=user_id,
                coded_user_id=link_for_other
            )
            )
            await state.set_state(FSMFillForm.participated)




@dp.message(CommandStart(), StateFilter(FSMFillForm.participated))
async def continue_paricipation(message: Message, state: FSMContext):
    args = message.text.replace('/start ', '')
    if args == "return":
        data = await state.get_data()
        print(data)
        await message.answer(text="Поделитесь с другом этой ссылкой")
        await message.answer(text=data['coded_user_id'])
    else:
        await message.answer(text="Вы уже зареганы!")


#
# # Этот хэндлер будет срабатывать на любые сообщения, кроме тех
# # для которых есть отдельные хэндлеры, вне состояний
# @dp.message(StateFilter(default_state))
# async def send_echo(message: Message):
#     await message.reply(text='Извините, моя твоя не понимать')


# Запускаем поллинг
if __name__ == '__main__':
    dp.run_polling(bot)
