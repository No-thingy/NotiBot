import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv
from database import init_db, create_user, get_user
from handlers import (
    handle_start,
    handle_notes,
    handle_goals,
    handle_weather,
    handle_currency,
    handle_stats,
    handle_image,
    button_callback,
    handle_text,
    handle_cancel,
    handle_convert,
    handle_guess_number,
    handle_rps,
    handle_quiz
)

load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update.effective_message:
        await update.effective_message.reply_text(
            "❌ Извините, что-то пошло не так. Пожалуйста, попробуйте позже."
        )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        logger.info(f"Пользователь {user.username} начал работу с ботом")

        db_user = get_user(user.id)

        if not db_user:
            db_user = create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"Создан новый пользователь: {user.username}")

        keyboard = [
            [KeyboardButton("📝 Заметки"), KeyboardButton("🎯 Цели")],
            [KeyboardButton("🌤 Погода"), KeyboardButton("💱 Валюта")],
            [KeyboardButton("📊 Статистика"), KeyboardButton("🎮 Игры")],
            [KeyboardButton("❓ Помощь")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        welcome_message = (
            f"✨ Привет, {user.first_name}! ✨\n\n"
            "Я твой персональный помощник NotiBot! 🤖\n\n"
            "Вот что я умею:\n\n"
            "📝 Заметки - Создавать и управлять заметками\n"
            "🎯 Цели - Ставить и отслеживать цели\n"
            "🌤 Погода - Показывать актуальную погоду\n"
            "💱 Валюта - Отслеживать курсы валют\n"
            "📊 Статистика - Показывать твою статистику\n"
            "🎮 Игры - Сыграть в мини-игры\n\n"
            "📸 Также ты можешь отправлять мне фотографии, и я сохраню их для тебя!\n\n"
            "Выбери команду из меню ниже или используй кнопки быстрого доступа! 😊"
        )

        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_start: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


def main() -> None:
    try:
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("База данных успешно инициализирована")

        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            logger.error("TELEGRAM_TOKEN не найден в переменных окружения")
            raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения")
        
        logger.info("Создание приложения...")
        application = Application.builder().token(token).build()

        logger.info("Добавление обработчиков команд...")
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("notes", handle_notes))
        application.add_handler(CommandHandler("goals", handle_goals))
        application.add_handler(CommandHandler("weather", handle_weather))
        application.add_handler(CommandHandler("currency", handle_currency))
        application.add_handler(CommandHandler("convert", handle_convert))
        application.add_handler(CommandHandler("stats", handle_stats))
        application.add_handler(CommandHandler("cancel", handle_cancel))
        
        application.add_handler(CommandHandler("guess", handle_guess_number))
        application.add_handler(CommandHandler("rps", handle_rps))
        application.add_handler(CommandHandler("quiz", handle_quiz))
        
        application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        application.add_handler(CallbackQueryHandler(button_callback))
        
        application.add_error_handler(error_handler)

        commands = [
            ("start", "Начать работу с ботом"),
            ("notes", "Управление заметками"),
            ("goals", "Управление целями"),
            ("weather", "Узнать погоду"),
            ("currency", "Курсы валют"),
            ("convert", "Конвертация валют"),
            ("stats", "Статистика"),
            ("guess", "Игра 'Угадай число'"),
            ("rps", "Игра 'Камень-ножницы-бумага'"),
            ("quiz", "Викторина"),
            ("cancel", "Отменить текущее действие")
        ]
        application.bot.set_my_commands(commands)

        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise


if __name__ == '__main__':
    main()
