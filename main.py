import sqlite3
import time
import logging
import asyncio

from googletrans import Translator

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram import Bot, executor, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from db import BotDB

logging.basicConfig(level=logging.INFO)

translator = Translator()

BotDB = BotDB('db.db')

translate_word1 = ''
translate_word2 = ''
MSG = "Повторим слова, {}?"

TOKEN_API = '5815099989:AAEQ5vCjeKNhognqWdL51WUVhLrkW63m1HY'

bot = Bot(TOKEN_API)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Переключение между функциями добавления слов
class WordStateGroup(StatesGroup):
    word = State()
    word_translate = State()


# Переключение между функциями перевода слов
class TranslateStateGroup(StatesGroup):
    translate1 = State()
    translate2 = State()


# Переключение между функциями удаления слов
class DeleteStateGroup(StatesGroup):
    delete1 = State()
    delete2 = State()


# Старт
@dp.message_handler(commands='start')
async def start(message: types.Message):
    try:
        BotDB.add_user(message.from_user.id)
        start_text = f'Привет, {message.from_user.first_name}!\n'

    except sqlite3.IntegrityError:
        start_text = f'И снова привет, {message.from_user.first_name}!\n'

    start_text2 = "Этот бот помогает повторять слова на иностранных языках. "
    start_text3 = "Здесь Вы можете создавать свой список слов, а потом просматривать и повторять его.\n"
    start_text4 = "Вы можете добавлять перевод слов вручную или автоматически.\n"

    start_text5 = "Используйте кнопки ниже.\n"
    start_text6 = 'Нажав "Настроить ремайндер", Вы будете получать напоминания о повторении слов каждые 24 часа 7 дней '
    start_text6_2 = "подряд.\n"

    start_text7 = "Возвращайтесь на /start для возможности настройки,\n"
    start_text8 = "Чтобы просмотреть и повторить слова используйте /view"

    start_text = start_text + start_text2 + start_text3 + start_text4 + start_text5 + start_text6 + start_text6_2
    start_text += start_text7 + start_text8

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить слово", callback_data='add')],
        [InlineKeyboardButton("Удалить слово", callback_data='delete')],
        [InlineKeyboardButton("Настроить ремайндер", callback_data='remind')]
    ])

    await message.bot.send_message(message.from_user.id, start_text, reply_markup=ikb)


# Отмена действия
@dp.message_handler(commands='cancel', state="*")
async def cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить слово", callback_data='add')]
    ])

    await state.finish()
    await message.answer('Вы отменили действие!\nЧтобы просмотреть и повторить слова используйте /view',
                         reply_markup=ikb)


# Функция для добавления слов1
@dp.callback_query_handler(text='add')
async def add(callback: types.CallbackQuery) -> None:
    await callback.message.delete()

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/cancel')]
    ], resize_keyboard=True)

    await callback.message.answer("Напишите слово,\nЕсли хотите отменить действие, отправьте /cancel", reply_markup=kb)

    await WordStateGroup.word.set()


# Функция для добавления слов2
@dp.message_handler(state=WordStateGroup.word)
async def handle_word(message: types.Message) -> None:
    global translate_word1
    translate_word1 = message.text

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/cancel')],
        [KeyboardButton('/translate')]
    ], resize_keyboard=True)

    await message.reply('А теперь перевод,\nЕсли хотите отменить действие, отправьте /cancel,\nЕсли хотите перевести '
                        'автоматически, то нажмите /translate', reply_markup=kb)

    await WordStateGroup.next()


# Функция для удаления слов1
@dp.callback_query_handler(text='delete', state="*")
async def delete(callback: types.CallbackQuery) -> None:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/cancel')]
    ], resize_keyboard=True)

    await callback.message.answer("Напишите слово с его переводом, как написано в Вашем списке слов,\n"
                                  "Например, так: 'Hi - Привет' (без апострофов),\nЕсли хотите "
                                  "отменить действие, отправьте /cancel", reply_markup=kb)

    await DeleteStateGroup.last()


# Функция для удаления слов2
@dp.message_handler(state=DeleteStateGroup.delete2)
async def delete2(message: types.Message, state: FSMContext):
    BotDB.delete_record(message.from_user.id, message.text)

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить слово", callback_data='add')]
    ])

    await message.answer('Слово успешно удалено!\nЧтобы просмотреть и повторить слова используйте /view',
                         reply_markup=ikb)

    await state.finish()


# Функция для напоминания
@dp.callback_query_handler(text='remind')
async def remind(message: types.Message) -> None:
    await message.answer("Уведомления настроены")

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name

    logging.info(f'{user_id} {user_full_name} {time.asctime()}')

    for i in range(7):
        await asyncio.sleep(60 * 60 * 24)
        await bot.send_message(user_id, MSG.format(user_name))


# Функция для перевода слов1
@dp.message_handler(commands='translate', state='*')
async def translate(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/cancel')]
    ], resize_keyboard=True)

    await message.answer(
        'Напишите язык перевода на английском языке,\nЕсли хотите отменить действие, отправьте /cancel',
        reply_markup=kb)

    await TranslateStateGroup.last()


# Функция для перевода слов2
@dp.message_handler(state=TranslateStateGroup.translate2)
async def translate2(message: types.Message, state: FSMContext):
    global translate_word2

    lang = message.text
    result = ''

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/add_word')],
        [KeyboardButton('/cancel')]
    ], resize_keyboard=True)

    try:
        result = translator.translate(translate_word1, dest=lang)

    except ValueError:
        await message.answer('Неправильно указан язык', reply_markup=kb)
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton('/cancel')]
        ], resize_keyboard=True)

    translate_word2 = result.text

    await message.answer('Перевод слова: ' + result.text + '\nДобавить перевод?\nЕсли хотите отменить действие, '
                                                           'отправьте /cancel', reply_markup=kb)
    await state.finish()


# Функция для перевода слов3
@dp.message_handler(commands='add_word', state='*')
async def translate3(message: types.Message):
    BotDB.add_record(message.from_user.id, translate_word1 + " - " + translate_word2)

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить слово", callback_data='add')]
    ])

    await message.reply('Слово добавлено!\nЧтобы просмотреть и повторить слова используйте /view', reply_markup=ikb)


# Функция для добавления перевода слова
@dp.message_handler(state=WordStateGroup.word_translate)
async def handle_word_translate(message: types.Message, state: FSMContext) -> None:
    BotDB.add_record(message.from_user.id, translate_word1 + " - " + message.text)

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить слово", callback_data='add')]
    ])

    await message.reply('Слово добавлено!\nЧтобы просмотреть и повторить слова используйте /view', reply_markup=ikb)

    await state.finish()


# Функция для просмотра слов
@dp.message_handler(commands='view', state='*')
async def view(message: types.Message) -> None:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить слово", callback_data='add')],
        [InlineKeyboardButton("Удалить слово", callback_data='delete')]
    ])

    await message.answer("Ваш список слов:\n"+BotDB.get_records(message.from_user.id), reply_markup=ikb)


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp,
                           skip_updates=True)
