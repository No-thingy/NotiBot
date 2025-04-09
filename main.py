import telebot

bot = telebot.TeleBot('Токен')


@bot.message_handler(commands=['start'])
def main(chat):
    bot.send_message(chat.chat.id,
                     'Привет, меня зовут NotiBot! 😄\n'
                     'Я помогу тебе следить за курсом валют 💰, прогнозом погоды 🌤️ и управлять твоими заметками 📋 и целями 🎯. '
                     '\nЧем могу помочь? 🤖')


bot.polling(none_stop=True)
