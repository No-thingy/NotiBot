import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from database import create_user, get_user, Session
from database import Note, Goal, Image, Message
import requests
from datetime import datetime
import random

logger = logging.getLogger(__name__)

WAITING_FOR_NOTE = 1
WAITING_FOR_GOAL_TITLE = 2
WAITING_FOR_GOAL_DESCRIPTION = 3

GUESSING_NUMBER = 4
PLAYING_RPS = 5
PLAYING_QUIZ = 6

user_states = {}

QUIZ_QUESTIONS = [
    {
        "question": "Какая планета самая большая в Солнечной системе?",
        "options": ["Марс", "Юпитер", "Сатурн", "Земля"],
        "correct": 1
    },
    {
        "question": "Сколько континентов на Земле?",
        "options": ["5", "6", "7", "8"],
        "correct": 2
    },
    {
        "question": "Какое животное является символом России?",
        "options": ["Медведь", "Орел", "Волк", "Тигр"],
        "correct": 0
    }
]


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
            [
                InlineKeyboardButton("📝 Заметки", callback_data="notes"),
                InlineKeyboardButton("🎯 Цели", callback_data="goals")
            ],
            [
                InlineKeyboardButton("🌤 Погода", callback_data="weather"),
                InlineKeyboardButton("💱 Валюта", callback_data="currency")
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data="stats"),
                InlineKeyboardButton("🎮 Игры", callback_data="games_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

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
            "Выбери нужный раздел из меню ниже:"
        )

        if update.callback_query:
            await update.callback_query.message.edit_text(welcome_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_start: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        keyboard = [
            [
                InlineKeyboardButton("✏️ Создать заметку", callback_data="create_note"),
                InlineKeyboardButton("📋 Мои заметки", callback_data="list_notes")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "📚 Управление заметками\n\n"
            "Выбери, что хочешь сделать:"
        )
        
        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_notes: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_goals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        keyboard = [
            [
                InlineKeyboardButton("🎯 Создать цель", callback_data="create_goal"),
                InlineKeyboardButton("📋 Мои цели", callback_data="list_goals")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "🎯 Управление целями\n\n"
            "Выбери, что хочешь сделать:"
        )
        
        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_goals: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        api_key = os.getenv('WEATHER_API_KEY')
        if not api_key:
            logger.error("WEATHER_API_KEY не найден в переменных окружения")
            await update.message.reply_text("❌ Ошибка конфигурации. Пожалуйста, свяжитесь с администратором.")
            return

        city = context.args[0] if context.args else "Pskov"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            error_message = data.get('message', 'Неизвестная ошибка')
            logger.error(f"Ошибка при получении погоды: {error_message}")
            
            if "city not found" in error_message.lower():
                message = (
                    "❌ Город не найден. Проверьте правильность написания.\n"
                    "Пример: /weather Москва"
                )
            else:
                message = "❌ Не удалось получить данные о погоде. Попробуйте позже."
        else:
            message = (
                f"🌤 Погода в {data['name']}:\n\n"
                f"🌡 Температура: {data['main']['temp']}°C\n"
                f"💨 Ветер: {data['wind']['speed']} м/с\n"
                f"💧 Влажность: {data['main']['humidity']}%\n"
                f"📝 {data['weather'][0]['description'].capitalize()}\n\n"
                f"Чтобы узнать погоду в другом городе, используйте команду:\n"
                f"/weather <название города>"
            )

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_weather: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        api_key = os.getenv('CURRENCY_API_KEY')
        if not api_key:
            logger.error("CURRENCY_API_KEY не найден в переменных окружения")
            await update.message.reply_text("❌ Ошибка конфигурации. Пожалуйста, свяжитесь с администратором.")
            return

        base_currency = "RUB"
        target_currencies = ["USD", "EUR", "GBP", "CNY"]
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Ошибка при получении курсов валют: {data.get('error', 'Неизвестная ошибка')}")
            message = "❌ Не удалось получить курсы валют. Попробуйте позже."
        else:
            message = "💱 Курсы валют:\n\n"
            for currency in target_currencies:
                if currency in data['rates']:
                    rate = data['rates'][currency]
                    formatted_rate = f"{rate:.2f}"
                    message += f"1 {base_currency} = {formatted_rate} {currency}\n"

            message += "\n💡 Для конвертации валют используйте команду:\n"
            message += "/convert <сумма> <из валюты> <в валюту>\n"
            message += "Пример: /convert 100 USD RUB"

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_currency: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        session = Session()
        notes_count = session.query(Note).filter_by(user_id=user.id).count()
        goals_count = session.query(Goal).filter_by(user_id=user.id).count()
        images_count = session.query(Image).filter_by(user_id=user.id).count()
        messages_count = session.query(Message).filter_by(user_id=user.id).count()

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        stats_message = (
            f"📊 Твоя статистика\n\n"
            f"📝 Заметок: {notes_count}\n"
            f"🎯 Целей: {goals_count}\n"
            f"🖼 Изображений: {images_count}\n"
            f"💬 Сообщений: {messages_count}\n\n"
            f"Продолжай в том же духе! 💪"
        )

        if update.callback_query:
            await update.callback_query.message.edit_text(stats_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(stats_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_stats: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
        return
    note_id = context.user_data.get('note_id_for_image')
    if not note_id:
        await update.message.reply_text(
            "❌ Сначала выбери заметку через меню 'Мои заметки' и нажми '➕ Добавить изображение'\n\n"
            "Отправь сейчас мне текст заметки."
        )
        return
    photo = update.message.photo[-1]
    session = Session()

    image = Image(
        user_id=user.id,
        file_id=photo.file_id,
        description=update.message.caption or "Без описания",
        note_id=note_id
    )
    session.add(image)
    session.commit()
    del context.user_data['note_id_for_image']
    await update.message.reply_text("✅ Изображение успешно прикреплено к заметке!")
    keyboard = [[
        InlineKeyboardButton("🔙 Назад к заметкам", callback_data="list_notes")
    ]]
    await update.message.reply_text("📋 Вернуться к заметкам:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    try:
        query = update.callback_query
        await query.answer()

        user = get_user(query.from_user.id)
        if not user:
            await query.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        if query.data == "main_menu":
            await handle_start(update, context)
            return

        elif query.data == "games_menu":
            await show_games_menu(update, context)
            return

        elif query.data == "notes":
            await handle_notes(update, context)
            return

        elif query.data == "goals":
            await handle_goals(update, context)
            return

        elif query.data == "weather":
            await handle_weather(update, context)
            return

        elif query.data == "currency":
            await handle_currency(update, context)
            return

        elif query.data == "stats":
            await handle_stats(update, context)
            return

        elif query.data.startswith("game_"):
            game_type = query.data.split("_")[1]
            if game_type == "guess":
                await handle_guess_number(update, context)
            elif game_type == "rps":
                await handle_rps(update, context)
            elif game_type == "quiz":
                await handle_quiz(update, context)
            return

        elif query.data.startswith("rps_"):
            user_choice = query.data.split("_")[1]
            choices = ["rock", "paper", "scissors"]
            bot_choice = random.choice(choices)
            
            result = determine_rps_winner(user_choice, bot_choice)
            
            emoji_map = {"rock": "✊", "paper": "✋", "scissors": "✌️"}
            result_message = (
                f"🎮 Результат игры:\n\n"
                f"Твой выбор: {emoji_map[user_choice]}\n"
                f"Мой выбор: {emoji_map[bot_choice]}\n\n"
                f"Результат: {result}\n\n"
                f"Чтобы сыграть еще раз, нажми на кнопку '🎮 Игры' или отправь /rps"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🎮 Игры", callback_data="games_menu"),
                    InlineKeyboardButton("✊ Сыграть еще раз", callback_data="game_rps")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(result_message, reply_markup=reply_markup)
            return

        elif query.data.startswith("quiz_"):
            if user.id not in user_states or user_states[user.id] != PLAYING_QUIZ:
                await query.message.edit_text("❌ Викторина не активна. Начни новую командой /quiz")
                return

            answer = int(query.data.split("_")[1])
            current_question = context.user_data.get('current_question', 0)
            correct_answer = QUIZ_QUESTIONS[current_question]['correct']

            if answer == correct_answer:
                context.user_data['quiz_score'] = context.user_data.get('quiz_score', 0) + 1
                result = "✅ Правильно!"
            else:
                result = "❌ Неверно!"

            await query.message.edit_text(
                f"{result}\n\n"
                f"Правильный ответ: {QUIZ_QUESTIONS[current_question]['options'][correct_answer]}"
            )

            context.user_data['current_question'] = current_question + 1
            await show_quiz_question(update, context)
            return

        elif query.data == "create_note":
            user_states[user.id] = WAITING_FOR_NOTE
            await query.message.edit_text(
                "✏️ Отправь мне текст заметки, которую хочешь сохранить.\n\n"
                "Чтобы отменить создание заметки, отправь /cancel"
            )
            return

        elif query.data == "create_goal":
            user_states[user.id] = WAITING_FOR_GOAL_TITLE
            await query.message.edit_text(
                "🎯 Введи название цели:\n\n"
                "Чтобы отменить создание цели, отправь /cancel"
            )
            return

        elif query.data == "list_notes":
            session = Session()
            notes = session.query(Note).filter_by(user_id=user.id).all()

            if not notes:
                await query.message.edit_text("📝 У тебя пока нет заметок.")
            else:
                for note in notes:
                    buttons = [
                        InlineKeyboardButton("❌ Удалить", callback_data=f"delete_note_{note.id}")
                    ]

                    if note.images:
                        buttons.insert(0, InlineKeyboardButton("📷 Открыть изображение",
                                                               callback_data=f"show_image_{note.id}"))
                    else:
                        buttons.insert(0, InlineKeyboardButton("➕ Добавить изображение",
                                                               callback_data=f"add_image_{note.id}"))

                    message = f"• {note.content}\n📅 {note.created_at.strftime('%d.%m.%Y %H:%M')}"
                    await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup([buttons]))

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="notes")]]
            await query.message.reply_text("Выбери заметку:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        elif query.data == "list_goals":
            session = Session()
            goals = session.query(Goal).filter_by(user_id=user.id).all()

            message = "🎯 Твои цели:\n\n"
            keyboard = []

            if not goals:
                message = "🎯 У тебя пока нет целей."
            else:
                for goal in goals:
                    message += f"• {goal.title}\n"
                    message += f"📄 {goal.description}\n"
                    message += f"📅 {goal.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    message += f"📌 Статус: {goal.status}\n"
                    message += "\n"
                    keyboard.append([
                        InlineKeyboardButton("❌ Удалить", callback_data=f"delete_goal_{goal.id}")
                    ])

            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="goals")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(message, reply_markup=reply_markup)
            return


        elif query.data.startswith("add_image_"):
            note_id = int(query.data.split("_")[2])
            context.user_data['note_id_for_image'] = note_id
            await query.message.reply_text("📷 Отправь изображение, которое хочешь прикрепить к этой заметке.")
            return

        elif query.data.startswith("show_image_"):
            note_id = int(query.data.split("_")[2])
            session = Session()
            image = session.query(Image).filter_by(note_id=note_id, user_id=user.id).first()
            if image:
                keyboard = [[
                    InlineKeyboardButton("🔙 Назад к заметкам", callback_data="list_notes")
                ]]
                await query.message.reply_photo(
                    image.file_id,
                    caption=f"📷 Изображение для заметки:\n{image.note.content}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.message.reply_text("❌ Изображение не найдено для этой заметки.")
            return


        elif query.data.startswith("delete_note_"):
            note_id = int(query.data.split("_")[2])
            session = Session()
            note = session.query(Note).filter_by(id=note_id, user_id=user.id).first()
            if note:
                session.delete(note)
                session.commit()
                await query.message.reply_text("✅ Заметка удалена.")
            else:
                await query.message.reply_text("❌ Заметка не найдена.")
            await handle_notes(update, context)
            return

        elif query.data.startswith("delete_goal_"):
            goal_id = int(query.data.split("_")[2])
            session = Session()
            goal = session.query(Goal).filter_by(id=goal_id, user_id=user.id).first()
            if goal:
                session.delete(goal)
                session.commit()
                await query.message.reply_text("✅ Цель удалена.")
            else:
                await query.message.reply_text("❌ Цель не найдена.")
            await handle_goals(update, context)
            return

    except Exception as e:
        logger.error(f"Ошибка в button_callback: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages and quick command buttons."""
    try:
        text = update.message.text
        user = get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        if user.id in user_states:
            if user_states[user.id] == WAITING_FOR_NOTE:
                if not text:
                    await update.message.reply_text("❌ Заметка не может быть пустой. Попробуйте еще раз.")
                    return
                
                session = Session()
                note = Note(
                    user_id=user.id,
                    content=text
                )
                
                session.add(note)
                session.commit()
                
                del user_states[user.id]
                
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="notes")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "✅ Заметка успешно сохранена!",
                    reply_markup=reply_markup
                )
                return

            elif user_states[user.id] == WAITING_FOR_GOAL_TITLE:
                if not text:
                    await update.message.reply_text("❌ Название цели не может быть пустым. Попробуйте еще раз.")
                    return
                
                context.user_data['goal_title'] = text
                user_states[user.id] = WAITING_FOR_GOAL_DESCRIPTION
                
                await update.message.reply_text(
                    "📝 Теперь введи описание цели:\n\n"
                    "Чтобы отменить создание цели, отправь /cancel"
                )
                return

            elif user_states[user.id] == WAITING_FOR_GOAL_DESCRIPTION:
                if not text:
                    await update.message.reply_text("❌ Описание цели не может быть пустым. Попробуйте еще раз.")
                    return
                
                session = Session()
                goal = Goal(
                    user_id=user.id,
                    title=context.user_data['goal_title'],
                    description=text,
                    status="В процессе"
                )
                
                session.add(goal)
                session.commit()
                
                del context.user_data['goal_title']
                del user_states[user.id]
                
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="goals")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ Цель успешно создана!",
                    reply_markup=reply_markup
                )
                return

            elif user_states[user.id] == GUESSING_NUMBER:
                try:
                    guess = int(text)
                    context.user_data['attempts'] = context.user_data.get('attempts', 0) + 1
                    
                    if guess < context.user_data['secret_number']:
                        await update.message.reply_text("⬆️ Загаданное число больше!")
                    elif guess > context.user_data['secret_number']:
                        await update.message.reply_text("⬇️ Загаданное число меньше!")
                    else:
                        attempts = context.user_data['attempts']
                        keyboard = [
                            [
                                InlineKeyboardButton("🎮 Игры", callback_data="games_menu"),
                                InlineKeyboardButton("🎲 Сыграть еще раз", callback_data="game_guess")
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(
                            f"🎉 Поздравляю! Ты угадал число за {attempts} попыток!",
                            reply_markup=reply_markup
                        )
                        del user_states[user.id]
                        del context.user_data['secret_number']
                        del context.user_data['attempts']
                except ValueError:
                    await update.message.reply_text("❌ Пожалуйста, введи число!")
                return

        if text == "📝 Заметки":
            await handle_notes(update, context)
        elif text == "🎯 Цели":
            await handle_goals(update, context)
        elif text == "🌤 Погода":
            await handle_weather(update, context)
        elif text == "💱 Валюта":
            await handle_currency(update, context)
        elif text == "📊 Статистика":
            await handle_stats(update, context)
        elif text == "🎮 Игры":
            await show_games_menu(update, context)
        elif text == "❓ Помощь":
            await handle_start(update, context)
        else:
            session = Session()
            message = Message(
                user_id=user.id,
                text=text,
                created_at=datetime.now()
            )
            session.add(message)
            session.commit()
            
            await update.message.reply_text(
                "📝 Ваше сообщение сохранено!\n\n"
                "Используйте кнопки быстрого доступа или команды для работы с ботом."
            )
            
    except Exception as e:
        logger.error(f"Ошибка в handle_text: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel command."""
    try:
        user = get_user(update.effective_user.id)
        if user and user.id in user_states:
            if 'goal_title' in context.user_data:
                del context.user_data['goal_title']
            del user_states[user.id]
            
            await update.message.reply_text(
                "❌ Операция отменена.\n\n"
                "Чтобы начать заново, используй соответствующую команду."
            )
    except Exception as e:
        logger.error(f"Ошибка в handle_cancel: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert currency."""
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        if len(context.args) != 3:
            await update.message.reply_text(
                "❌ Неправильный формат команды.\n"
                "Используйте: /convert <сумма> <из валюты> <в валюту>\n"
                "Пример: /convert 100 USD RUB"
            )
            return

        amount, from_currency, to_currency = context.args
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        try:
            amount = float(amount)
        except ValueError:
            await update.message.reply_text("❌ Сумма должна быть числом")
            return

        api_key = os.getenv('CURRENCY_API_KEY')
        if not api_key:
            logger.error("CURRENCY_API_KEY не найден в переменных окружения")
            await update.message.reply_text("❌ Ошибка конфигурации. Пожалуйста, свяжитесь с администратором.")
            return

        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Ошибка при получении курсов валют: {data.get('error', 'Неизвестная ошибка')}")
            await update.message.reply_text("❌ Не удалось получить курсы валют. Попробуйте позже.")
            return

        if to_currency not in data['rates']:
            await update.message.reply_text(f"❌ Валюта {to_currency} не найдена")
            return

        rate = data['rates'][to_currency]
        converted_amount = amount * rate

        result_message = (
            f"💱 Результат конвертации:\n\n"
            f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}\n"
            f"Курс: 1 {from_currency} = {rate:.4f} {to_currency}"
        )

        await update.message.reply_text(result_message)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_convert: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при конвертации валют.\n"
            "Проверьте правильность команды и попробуйте снова."
        )


def determine_rps_winner(user_choice: str, bot_choice: str) -> str:
    if user_choice == bot_choice:
        return "Ничья! 🤝"
    
    winning_combinations = {
        "rock": "scissors",
        "paper": "rock",
        "scissors": "paper"
    }
    
    if winning_combinations[user_choice] == bot_choice:
        return "Ты победил! 🎉"
    else:
        return "Я победил! 😎"


async def show_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        current_question = context.user_data.get('current_question', 0)
        if current_question >= len(QUIZ_QUESTIONS):
            score = context.user_data.get('quiz_score', 0)
            total = len(QUIZ_QUESTIONS)
            
            if update.effective_user.id in user_states:
                del user_states[update.effective_user.id]

            keyboard = [
                [
                    InlineKeyboardButton("🎮 Игры", callback_data="games_menu"),
                    InlineKeyboardButton("❓ Сыграть еще раз", callback_data="game_quiz")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"🎉 Викторина завершена!\n\n"
                f"Твой результат: {score} из {total} правильных ответов!\n\n"
                f"Чтобы сыграть еще раз, нажми на кнопку ниже или отправь /quiz"
            )
            
            if update.callback_query:
                await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup)
            return

        question = QUIZ_QUESTIONS[current_question]
        keyboard = []
        for i, option in enumerate(question['options']):
            keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_{i}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"❓ Вопрос {current_question + 1} из {len(QUIZ_QUESTIONS)}:\n\n"
            f"{question['question']}"
        )
        
        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в show_quiz_question: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def show_games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        keyboard = [
            [
                InlineKeyboardButton("🎲 Угадай число", callback_data="game_guess"),
                InlineKeyboardButton("✊ Камень-ножницы-бумага", callback_data="game_rps")
            ],
            [InlineKeyboardButton("❓ Викторина", callback_data="game_quiz")],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "🎮 Выбери игру:\n\n"
            "🎲 Угадай число - попробуй угадать загаданное число от 1 до 100\n"
            "✊ Камень-ножницы-бумага - классическая игра\n"
            "❓ Викторина - проверь свои знания\n\n"
            "Или используй команды:\n"
            "/guess - начать игру 'Угадай число'\n"
            "/rps - начать игру 'Камень-ножницы-бумага'\n"
            "/quiz - начать викторину"
        )

        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Ошибка в show_games_menu: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_guess_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        context.user_data['secret_number'] = random.randint(1, 100)
        context.user_data['attempts'] = 0
        user_states[user.id] = GUESSING_NUMBER

        message = (
            "🎮 Игра 'Угадай число'!\n\n"
            "Я загадал число от 1 до 100.\n"
            "Попробуй угадать его!\n\n"
            "Чтобы отменить игру, отправь /cancel"
        )

        if update.callback_query:
            await update.callback_query.message.edit_text(message)
        else:
            await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Ошибка в handle_guess_number: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_rps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        keyboard = [
            [
                InlineKeyboardButton("✊", callback_data="rps_rock"),
                InlineKeyboardButton("✋", callback_data="rps_paper"),
                InlineKeyboardButton("✌️", callback_data="rps_scissors")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            "🎮 Игра 'Камень-ножницы-бумага'!\n\n"
            "Выбери свой ход:"
        )

        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в handle_rps: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ Сначала начни использовать бота командой /start")
            return

        context.user_data['quiz_score'] = 0
        context.user_data['current_question'] = 0
        user_states[user.id] = PLAYING_QUIZ

        await show_quiz_question(update, context)
    except Exception as e:
        logger.error(f"Ошибка в handle_quiz: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
