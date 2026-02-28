# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ================= НАСТРОЙКИ (ОБЯЗАТЕЛЬНО ЗАПОЛНИ) =================
TOKEN = "8347761584:AAEp1W7l5wFWh5Y5-3OU6L2isE7uRuET-Dw"
ADMIN_GROUP_ID = -1003867217861   # Группа для заявок
WELCOME_GROUP_ID = -1003828359079 # ВТОРАЯ ГРУППА (для приветствий)
CHANNEL_ID = "@NevermoreCh"
CHANNEL_LINK = "https://t.me/NevermoreCh"
CHAT_LINK = "https://t.me/+E8l-GaHB9iBlMjFi"

# Стикеры
S_SUCCESS = "CAACAgQAAxkBAAJKCWmbQHwyxWL5oiNiktj23MP0PMPmAAKGGAAC6rJwU_0CbLv7pF3COgQ"
S_REJECT = "CAACAgQAAxkBAAJKC2mbQbHl0VeA9kfOfsBpxQJ4XP3qAAIFGAAC11NxUxqt1ievRv-2OgQ"

# Премиум Эмодзи
E_SKULL = "5251591568065845575"
E_FIRE = "5253458624709154474"
E_CHECK = "5267120447526301429"
E_CROSS = "5210952531676504517"
E_ANGRY = "5370689396276205290"

def e(eid): return f'<tg-emoji emoji-id="{eid}">▫️</tg-emoji>'

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Состояния
class Form(StatesGroup):
    wait_nickname = State()
    wait_license = State()
    wait_application = State()
    confirm = State()

class AdminAction(StatesGroup):
    wait_reason = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def is_subscribed(user_id):
    try:
        m = await bot.get_chat_member(CHANNEL_ID, user_id)
        return m.status in ["member", "administrator", "creator"]
    except: return False

def extract_hobby(text):
    """Вырезает пункт 'Чем занимаешься в майнкрафте' из анкеты"""
    match = re.search(r"4\.(.*?)(?=5\.|\Z)", text, re.DOTALL | re.IGNORECASE)
    if match: return match.group(1).strip()
    return "Просто хороший игрок"

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📝 ЗАПОЛНИТЬ АНКЕТУ", callback_data="form_start"))
    kb.row(InlineKeyboardButton(text="👤 ПРОФИЛЬ", callback_data="me"),
           InlineKeyboardButton(text="📋 ИНФО", callback_data="info"))
    return kb.as_markup()

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start"))
async def start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="ПОДПИСАТЬСЯ", url=CHANNEL_LINK))
        return await message.answer(f"<b>Доступ закрыт!</b>\nПодпишись на канал сервера: {CHANNEL_ID}", reply_markup=kb.as_markup())

    await message.answer(
        f"<b>{e(E_SKULL)} NEVERMORE HOUSE 1.21.1 {e(E_SKULL)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Привет! Это официальный бот для подачи заявок.\n"
        f"Тщательно заполняй анкету, админы смотрят всё.\n\n"
        f"<b>Готов начать?</b>", reply_markup=get_main_kb()
    )

@dp.callback_query(F.data == "info")
async def info(callback: types.CallbackQuery):
    await callback.message.answer(f"<b>NEVERMORE 1.21.1</b>\nВанильное выживание без приватов.\nСоблюдай правила и не мешай другим.")
    await callback.answer()

@dp.callback_query(F.data == "me")
async def my_profile(callback: types.CallbackQuery):
    await callback.message.answer(f"<b>Твой ID:</b> <code>{callback.from_user.id}</code>\n<b>Ник:</b> @{callback.from_user.username}")
    await callback.answer()

# --- ПРОЦЕСС АНКЕТЫ ---
@dp.callback_query(F.data == "form_start")
async def f_step1(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(f"<b>Введи свой ник в Minecraft:</b>")
    await state.set_state(Form.wait_nickname)
    await callback.answer()

@dp.message(Form.wait_nickname)
async def f_step2(message: types.Message, state: FSMContext):
    nick = message.text.strip()
    if len(nick) < 3: return await message.answer("Ник слишком короткий!")
    
    body = f"https://mc-heads.net/body/{nick}/right"
    head = f"https://mc-heads.net/avatar/{nick}"
    await state.update_data(nick=nick, head=head, body=body)
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="ЛИЦЕНЗИЯ", callback_data="lic_y"),
           InlineKeyboardButton(text="ПИРАТКА", callback_data="lic_n"))
    await message.answer_photo(photo=body, caption=f"Твой скин найден. Тип аккаунта?", reply_markup=kb.as_markup())
    await state.set_state(Form.wait_license)

@dp.callback_query(Form.wait_license)
async def f_step3(callback: types.CallbackQuery, state: FSMContext):
    lic = "Лицензия" if callback.data == "lic_y" else "Пиратка"
    await state.update_data(lic=lic)
    
    template = (
        "1. Возраст (от 12 лет): \n"
        "2. Имя: \n"
        "3. О себе: \n"
        "4. Чем занимаешься в майнкрафте: \n"
        "5. Часовой пояс: \n"
        "6. Активность (ч/день): \n"
        "7. Откуда узнали: \n"
        "8. Почему решили вступить именно к нам: \n"
        "9. Пол: \n"
        "10. Страна: "
    )
    
    await callback.message.answer(
        f"<b>{e(E_FIRE)} ШАГ 2: АНКЕТА</b>\n\n"
        f"Нажми на текст ниже, чтобы скопировать. Заполни все пункты и отправь одним сообщением.\n\n"
        f"<code>{template}</code>"
    )
    await state.set_state(Form.wait_application)
    await callback.answer()

@dp.message(Form.wait_application)
async def f_step4(message: types.Message, state: FSMContext):
    if len(message.text) < 50 or "Имя:" not in message.text:
        return await message.answer(f"Без Приколов давай пиши нормально анкету {e(E_ANGRY)}")

    await state.update_data(full_text=message.text)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="ОТПРАВИТЬ ✅", callback_data="confirm_all"),
           InlineKeyboardButton(text="ИЗМЕНИТЬ ❌", callback_data="form_start"))
    
    await message.answer(f"<b>ПРОВЕРКА:</b>\n\n{message.text}\n\n<b>Отправляем админам?</b>", reply_markup=kb.as_markup())
    await state.set_state(Form.confirm)

@dp.callback_query(Form.confirm, F.data == "confirm_all")
async def f_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    adm_kb = InlineKeyboardBuilder()
    adm_kb.add(InlineKeyboardButton(text="✅ ПРИНЯТЬ", callback_data=f"accept_{callback.from_user.id}"))
    adm_kb.add(InlineKeyboardButton(text="❌ ОТКАЗ", callback_data=f"reject_{callback.from_user.id}"))

    admin_msg = (
        f"<b>{e(E_FIRE)} НОВАЯ ЗАЯВКА</b>\n"
        f"👤 Юзер: @{callback.from_user.username}\n"
        f"🎮 Ник: <code>{data['nick']}</code> | {data['lic']}\n\n"
        f"<b>АНКЕТА:</b>\n{data['full_text']}"
    )

    media = [InputMediaPhoto(media=data['head'], caption=admin_msg), InputMediaPhoto(media=data['body'])]
    await bot.send_media_group(ADMIN_GROUP_ID, media=media)
    await bot.send_message(ADMIN_GROUP_ID, f"Решение по <code>{data['nick']}</code>:", reply_markup=adm_kb.as_markup())

    await callback.message.answer(f"<b>Готово!</b> Анкета на рассмотрении. Ожидай уведомления.")
    await bot.send_sticker(callback.from_user.id, S_SUCCESS)
    await state.clear()
    await callback.answer()

# --- АДМИНКА ---
@dp.callback_query(F.data.startswith("accept_"))
async def adm_accept(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    # Вытаскиваем данные из сообщения админа (костыль, но рабочий без БД)
    text = callback.message.reply_to_message.caption if callback.message.reply_to_message else ""
    
    # Пытаемся достать ник и инфо
    mc_nick = re.search(r"Ник: (.*?) \|", callback.message.text).group(1) if "Ник:" in callback.message.text else "Игрок"
    hobby = extract_hobby(callback.message.text)

    # 1. Пишем игроку
    await bot.send_message(uid, f"<b>{e(E_CHECK)} ТЫ ПРИНЯТ!</b>\nДобро пожаловать на Nevermore House 1.21.1\n\n<b>Чат:</b> {CHAT_LINK}")
    
    # 2. Пишем во ВТОРУЮ ГРУППУ
    welcome_text = (
        f"<b>{e(E_FIRE)} НОВЫЙ ИГРОК!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Добро пожаловать, <a href='tg://user?id={uid}'>участник</a>!\n"
        f"🎮 Ник в игре: <code>{mc_nick}</code>\n"
        f"🛠 Занимается в майнкрафте: <i>{hobby}</i>\n\n"
        f"Приятной игры на <b>Nevermore</b>!"
    )
    await bot.send_message(WELCOME_GROUP_ID, welcome_text)

    await callback.message.edit_text(f"✅ Игрок {mc_nick} одобрен!")

@dp.callback_query(F.data.startswith("reject_"))
async def adm_reject(callback: types.CallbackQuery, state: FSMContext):
    uid = int(callback.data.split("_")[1])
    await state.update_data(target_uid=uid)
    await callback.message.answer("<b>Напиши причину:</b>\n(Причина: текст)")
    await state.set_state(AdminAction.wait_reason)
    await callback.answer()

@dp.message(AdminAction.wait_reason, F.text.lower().startswith("причина:"))
async def adm_reason_send(message: types.Message, state: FSMContext):
    data = await state.get_data()
    reason = message.text.split(":", 1)[1].strip()
    
    await bot.send_message(data['target_uid'], f"<b>{e(E_CROSS)} ОТКАЗ</b>\nПричина: {reason}")
    await bot.send_sticker(data['target_uid'], S_REJECT)
    await message.answer("Уведомление отправлено.")
    await state.clear()

# --- ЗАПУСК ---
async def main():
    print("Nevermore Bot 1.21.1 запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass