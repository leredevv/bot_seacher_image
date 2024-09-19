import telebot
import requests

WEATHER_API_KEY = 'token'
api_key = 'key'
bot = telebot.TeleBot('token2')
google_api_key = 'key2'
google_cx = 'cx'

# словарь для хранения истории запросов пользователей
history = {}

@bot.message_handler(commands=['num'])
def start_handler(message):
    bot.send_message(message.chat.id, "Введите номер телефона в формате +1234567890:")


@bot.message_handler(regexp="^\+\d{11}$")
def phone_handler(message):
    phone_number = message.text
    url = f'http://apilayer.net/api/validate?access_key={api_key}&number={phone_number}'
    response = requests.get(url)
    data = response.json()
    if data['valid']:
        country = data['country_name']
        location = data['location']
        carrier = data['carrier']
        bot.send_message(message.chat.id, f"Страна: {country}\nМестоположение: {location}\nОператор связи: {carrier}")
    else:
        bot.send_message(message.chat.id, "Неверный номер телефона")


@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Поиск', request_location=False, request_contact=False), row_width=2)
    bot.send_message(message.chat.id, '👋 | Привет! Я бот для поиска изображений. Нажми кнопку "Поиск", чтобы начать поиск.',
                     reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def search_images(message):
    if message.text == 'Поиск':
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, '🔍 | Введите запрос для поиска изображений:')
        bot.register_next_step_handler(message, process_query)
    elif message.text == '/history':
        # выводим историю запросов текущего пользователя
        user_id = message.chat.id
        if user_id in history:
            bot.send_message(user_id, '📜 | История ваших запросов:\n' + '\n'.join(history[user_id]))
        else:
            bot.send_message(user_id, '📜 | История ваших запросов пуста.')
    else:
        bot.send_message(message.chat.id, '🔍 | Используйте кнопку "Поиск", чтобы начать поиск.')


def process_query(message):
    query = message.text
    images = search_images_google(query)
    if images:
        for image in images:
            response = requests.get(image)
            if response.status_code == 200:
                file = response.content
                try:
                    bot.send_photo(message.chat.id, file)
                except telebot.apihelper.ApiException:
                    bot.send_message(message.chat.id, '🔴 | Ошибка при отправке фотографии.')
            else:
                bot.send_message(message.chat.id, '🔴 | Ошибка при получении фотографии.')
        # добавляем запрос в историю текущего пользователя
        user_id = message.chat.id
        if user_id not in history:
            history[user_id] = []
        history[user_id].append(query)
    else:
        bot.send_message(message.chat.id, '❌ | По вашему запросу ничего не найдено.')
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Поиск', request_location=False, request_contact=False), row_width=2)
    bot.send_message(message.chat.id, '🔍 | Нажми кнопку "Поиск", чтобы начать новый поиск.', reply_markup=markup)

def search_images_google(query):
    url = f'https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_cx}&q={query}&searchType=image'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        images = [item['link'] for item in data.get('items', [])]
        return images
    else:
        return None



bot.polling()
