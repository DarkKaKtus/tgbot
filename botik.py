import pip
pip.main(['install', 'pytelegrambotapi'])
import telebot
from telebot import types
import sqlite3
import time
import logging
bot = telebot.TeleBot('TOKEN_BOTA', skip_pending=True)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
users_data = {}

conn = sqlite3.connect('clubs.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS clubs
             (club_name text, cups_required integer, admin_id integer)''')
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id integer PRIMARY KEY, username text, club text)''')
c.execute('''CREATE TABLE IF NOT EXISTS user_photos
             (user_id integer, photo_id integer)''')
conn.close()

conn = sqlite3.connect('clubs.db')
c = conn.cursor()
clubs = c.execute("SELECT * FROM clubs").fetchall()
conn.close()

selected_club = {}
last_photo_time = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    username = message.chat.username

    if user_id == bot.get_me().id:
        return
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        clubs = c.execute("SELECT * FROM clubs").fetchall()
    keyboard = types.InlineKeyboardMarkup()
    for i in range(0, len(clubs), 2):
        buttons = [types.InlineKeyboardButton(club[0], callback_data=club[0]) for club in clubs[i:i+2]]
        keyboard.add(*buttons)
    caption = '✨Выбери клуб, в который ты хочешь подать заявку✨ \n \n Наши клубы:\n'
    for club in clubs:
        caption += f"—\n{club[0]} Wallace: \nВход: {club[1]}🏆\n"
#Вместо photo_tut надо вставить ссылку на действующую картинку
    bot.send_photo(message.chat.id, 'Photo_TUT', caption=caption, reply_markup=keyboard)

@bot.message_handler(commands=['setlimit'])
def set_limit(message):
    user_id = message.chat.id
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        club = c.execute("SELECT * FROM clubs WHERE admin_id = ?", (user_id,)).fetchone()
    if club is not None:
        bot.send_message(user_id, "Пожалуйста, введите новый лимит кубков для вашего клуба.")
        bot.register_next_step_handler(message, update_limit, club[0])
    else:
        bot.send_message(user_id, "Извините, эта команда доступна только администраторам клуба.")
        conn.commit()
        conn.close()

def update_limit(message, club_name):
    try:
        new_limit = int(message.text)
        with sqlite3.connect('clubs.db') as conn:
            c = conn.cursor()
            c.execute("UPDATE clubs SET cups_required = ? WHERE club_name = ?", (new_limit, club_name))
        bot.send_message(message.chat.id, f"Лимит кубков для клуба {club_name} успешно обновлен до {new_limit}.")
    except ValueError:
        bot.send_message(message.chat.id, "Извините, я не смог распознать это число. Пожалуйста, попробуйте еще раз.")
        conn.commit()
        conn.close()

#ID_Admina поменять на нужных вам администраторов, например вас и заместителя, или же можете оставить только свой ID
admin_ids = [ID_Admina_One, ID_Admina_Two]

selected_club_to_change_admin = {}
selected_club_to_delete = {}
changing_admin = {}
new_club_info = {}
selected_club_to_change_name = {}
message_to_delete = {}
@bot.message_handler(commands=['login228'])
def login(message):
    if message.from_user.id in admin_ids:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Изменить администратора клуба", callback_data="change_admin"))
        keyboard.add(types.InlineKeyboardButton("Изменить название клуба", callback_data="change_name"))
        keyboard.add(types.InlineKeyboardButton("Добавить новый клуб", callback_data="add_club"))
        keyboard.add(types.InlineKeyboardButton("Удалить клуб", callback_data="delete_club"))
        bot.send_message(message.chat.id, "Добро пожаловать в главное меню управления клубами.\nПидорас.", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Извините, у вас нет доступа к этой команде.")


def get_new_club_name(message):
    new_club_info[message.chat.id] = {"name": message.text}
    bot.send_message(message.chat.id, "Пожалуйста, введите количество кубков для нового клуба.\n/login228")
    bot.register_next_step_handler(message, get_new_club_cups)

def get_new_club_cups(message):
    new_club_info[message.chat.id]["cups"] = int(message.text)
    bot.send_message(message.chat.id, "Пожалуйста, введите ID администратора для нового клуба.\n/login228")
    bot.register_next_step_handler(message, get_new_club_admin)

def get_new_club_admin(message):
    new_club_info[message.chat.id]["admin_id"] = int(message.text)
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO clubs (club_name, cups_required, admin_id) VALUES (?, ?, ?)", (new_club_info[message.chat.id]["name"], new_club_info[message.chat.id]["cups"], new_club_info[message.chat.id]["admin_id"]))
    bot.send_message(message.chat.id, f"Новый клуб {new_club_info[message.chat.id]['name']} был успешно добавлен.\n/login228")
    del new_club_info[message.chat.id]
    conn.commit()
    conn.close()

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "change_admin":
        changing_admin[call.message.chat.id] = True
        with sqlite3.connect('clubs.db') as conn:
            c = conn.cursor()
            clubs = c.execute("SELECT * FROM clubs").fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for club in clubs:
            keyboard.add(types.InlineKeyboardButton(club[0], callback_data=f"select_{club[0]}"))
        bot.send_message(call.message.chat.id, "Пожалуйста, выберите клуб, администратора которого вы хотите изменить.", reply_markup=keyboard)
    elif call.data.startswith("select_") and call.message.chat.id in changing_admin:
        selected_club_to_change_admin[call.message.chat.id] = call.data.split("_")[1]
        bot.send_message(call.message.chat.id, "Пожалуйста, отправьте новый ID администратора.\n/login228")
    elif call.data == "delete_club":
        with sqlite3.connect('clubs.db') as conn:
            c = conn.cursor()
            clubs = c.execute("SELECT * FROM clubs").fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for club in clubs:
            keyboard.add(types.InlineKeyboardButton(club[0], callback_data=f"select_delete_{club[0]}"))
        bot.send_message(call.message.chat.id, "Пожалуйста, выберите клуб, который вы хотите удалить.", reply_markup=keyboard)
    elif call.data.startswith("select_delete_"):
        selected_club_to_delete[call.message.chat.id] = call.data.split("_")[2]
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Да", callback_data="confirm_delete"))
        keyboard.add(types.InlineKeyboardButton("Нет", callback_data="cancel_delete"))
        bot.send_message(call.message.chat.id, f"Вы уверены, что хотите удалить клуб {selected_club_to_delete[call.message.chat.id]}?", reply_markup=keyboard)
    elif call.data == "confirm_delete":
        with sqlite3.connect('clubs.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM clubs WHERE club_name = ?", (selected_club_to_delete[call.message.chat.id],))
        bot.send_message(call.message.chat.id, f"Клуб {selected_club_to_delete[call.message.chat.id]} был успешно удален.\n/login228")
        del selected_club_to_delete[call.message.chat.id]
    elif call.data == "cancel_delete":
        bot.send_message(call.message.chat.id, "Удаление клуба было отменено.\n/login228")
        del selected_club_to_delete[call.message.chat.id]
    if call.data == "add_club":
        bot.send_message(call.message.chat.id, "Пожалуйста, введите название нового клуба.")
        bot.register_next_step_handler(call.message, get_new_club_name)
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        clubs = c.execute("SELECT * FROM clubs").fetchall()
        if call.data in [club[0] for club in clubs]:
            selected_club[call.message.chat.id] = call.data
            c.execute("UPDATE users SET club = ? WHERE user_id = ?", (call.data, call.message.chat.id))
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # Получаем информацию о выбранном клубе
            club_info = c.execute("SELECT * FROM clubs WHERE club_name = ?", (call.data,)).fetchone()
            club_name = club_info[0]
            club_limit = club_info[1]
            bot.send_message(call.message.chat.id, f"{club_name} прекрасный выбор!\nВход: {club_limit}🏆 \nЧтобы вступить, отправьте скриншот вашего профиля.")
        elif call.data.startswith("accept"):
            user_id = call.data.split("_")[1]
            bot.send_message(user_id, "✅Поздравляем, вы были приняты в клуб!")
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вы успешно забайтили его на вступление...")
        elif call.data.startswith("reject"):
            user_id = call.data.split("_")[1]
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пожалуйста, введите причину отклонения.")
            bot.register_next_step_handler(call.message, reject_reason, user_id)
        elif call.data == "start":
            send_welcome(call.message)
        elif call.data == "change_photo":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Пожалуйста, отправьте новую фотографию.")
        elif call.data == "change_club":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message)
    if call.data == "change_name":
        with sqlite3.connect('clubs.db') as conn:
            c = conn.cursor()
            clubs = c.execute("SELECT * FROM clubs").fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for club in clubs:
            keyboard.add(types.InlineKeyboardButton(club[0], callback_data=f"select_name_{club[0]}"))
        bot.send_message(call.message.chat.id, "Пожалуйста, выберите клуб, название которого вы хотите изменить.", reply_markup=keyboard)
    elif call.data.startswith("select_name_"):
        selected_club_to_change_name[call.message.chat.id] = call.data.split("_")[2]
        bot.send_message(call.message.chat.id, "Пожалуйста, введите новое название клуба.")
    if call.data.startswith("send_"):
        user_id = int(call.data.split('_')[1])
        with sqlite3.connect('clubs.db') as conn:
            c = conn.cursor()
            photo_id = c.execute("SELECT photo_id FROM user_photos WHERE user_id = ?", (user_id,)).fetchone()[0]
            for club in clubs:
                if club[0] == selected_club[call.message.chat.id]:
                    bot.send_photo(club[2], photo_id, f"{club[0]}\nСкриншот от очередного чемпиона: @{call.from_user.username}\nID: tg://openmessage?user_id={user_id}")
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(text="Принять", callback_data=f"accept_{user_id}"),
                               types.InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}"))
                    bot.send_message(club[2], "Принять или отклонить?", reply_markup=markup)
            bot.send_message(call.message.chat.id, f"✅Спасибо! \nВаша заявка была отправлена администратору, скоро она будет рассмотрена и вам ответят.❤️")
            if call.message.chat.id in message_to_delete:
                bot.delete_message(chat_id=call.message.chat.id, message_id=message_to_delete[call.message.chat.id])
                del message_to_delete[call.message.chat.id]
            if call.data.startswith("change_"):
                user_id = int(call.data.split('_')[1])
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(call.message.chat.id, "Пожалуйста, отправьте новую фотографию.")

@bot.message_handler(func=lambda message: message.chat.id in selected_club_to_change_name)
def change_club_name(message):
    new_club_name = message.text
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE clubs SET club_name = ? WHERE club_name = ?", (new_club_name, selected_club_to_change_name[message.chat.id]))
    bot.send_message(message.chat.id, f"Название клуба {selected_club_to_change_name[message.chat.id]} было успешно изменено на {new_club_name}.\n/login228")
    del selected_club_to_change_name[message.chat.id]

@bot.message_handler(func=lambda message: message.chat.id in selected_club_to_change_admin)
def change_admin(message):
    new_admin_id = int(message.text)
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE clubs SET admin_id = ? WHERE club_name = ?", (new_admin_id, selected_club_to_change_admin[message.chat.id]))
    bot.send_message(message.chat.id, f"Администратор клуба {selected_club_to_change_admin[message.chat.id]} был успешно изменен на tg://openmessage?user_id={new_admin_id}.\n/login228")
    del selected_club_to_change_admin[message.chat.id]


def reject_reason(message, user_id):
    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        user = c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if user is not None:
        username = user[1]
        bot.send_message(user_id, f"К сожалению, ваша заявка была отклонена \nПричина: {message.text}")
        bot.send_message(message.chat.id, f"Вы отклонили заявку пользователя \ntg://openmessage?user_id={user_id} \nПричина: {message.text}")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Подать заявку в другой клуб", callback_data="start"))
        bot.send_message(user_id, "Вы можете подать заявку в другой клуб:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Пользователь не найден в базе данных.")



@bot.message_handler(content_types=['photo'])
def handle_application(message):
    user_id = message.chat.id
    username = message.chat.username
    club = selected_club.get(user_id)

    if user_id == bot.get_me().id:
        return

    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, club) VALUES (?, ?, ?)",
                  (user_id, username, club))
        c.execute("UPDATE users SET username = ?, club = ? WHERE user_id = ?",
                  (username, club, user_id))
        conn.commit()

    now = time.time()
    if user_id in last_photo_time and now - last_photo_time[user_id] < 10:
        return
    last_photo_time[user_id] = now

    if club is None:
        bot.send_message(user_id, "Пожалуйста, сначала выберите клуб.")
        return

    with sqlite3.connect('clubs.db') as conn:
        c = conn.cursor()
        existing_user = c.execute("SELECT * FROM user_photos WHERE user_id = ?", (message.from_user.id,)).fetchone()
        if existing_user is None:
            c.execute("INSERT INTO user_photos (user_id, photo_id) VALUES (?, ?)", (message.from_user.id, message.photo[-1].file_id))
        else:
            c.execute("UPDATE user_photos SET photo_id = ? WHERE user_id = ?", (message.photo[-1].file_id, message.from_user.id))
        conn.commit()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Отправить", callback_data=f"send_{message.from_user.id}"),
               types.InlineKeyboardButton(text="Изменить скрин", callback_data="change_photo"))
    markup.add(types.InlineKeyboardButton("Выбрать другой клуб", callback_data="change_club"))
    msg = bot.send_message(message.chat.id, "Вы уверены, что хотите отправить эту фотографию?", reply_markup=markup)
    message_to_delete[message.chat.id] = msg.message_id


bot.polling()