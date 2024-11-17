from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
from config import *
import random

bot = TeleBot(API_TOKEN)

def gen_markup(prize_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=str(prize_id)))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = call.data
    user_id = call.message.chat.id

    if manager.add_winner(user_id, prize_id):
        img = manager.get_prize_img(prize_id)
        with open(f'img/{img}', 'rb') as photo:
            bot.send_photo(user_id, photo)
        bot.answer_callback_query(call.id, "Поздравляем! Вы получили приз!")
    else:
        bot.answer_callback_query(call.id, "Приз уже был получен другими пользователями.")

def send_message():
    prize_id, img = manager.get_random_prize()[:2]
    manager.mark_prize_used(prize_id)
    hide_img(img)
    users = manager.get_users()
    random.shuffle(users)  # Перемешиваем пользователей случайным образом
    for user in users[:3]:  # Отправляем сообщения только первым 3 пользователям
        with open(f'hidden_img/{img}', 'rb') as photo:
            bot.send_photo(user, photo, reply_markup=gen_markup(prize_id))

def shedule_thread():
    schedule.every(5).seconds.do(send_message)  # Каждые 5 секунд отправляем сообщения для тестирования
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегистрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждые 5 секунд тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")

def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
