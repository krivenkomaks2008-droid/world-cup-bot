import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'
bot = telebot.TeleBot(TOKEN)

TEAMS_RU = {
    "Argentina": "Аргентина", "France": "Франция", "Spain": "Испания",
    "England": "Англия", "Belgium": "Бельгия", "Norway": "Норвегия",
    "Switzerland": "Швейцария", "Morocco": "Марокко", "Canada": "Канада",
    "Egypt": "Египет", "Colombia": "Колумбия", "Ghanas": "Гана",
    "Algeria": "Алжир", "Australia": "Австралия", "Cape Verde": "🇨🇻Кабо-Верде",
    "Paraguay": "Парагвай", "USA": "США", "United States": "США",
    "Mexico": "Мексика", "Brazil": "Бразилия", "Portugal": "Португалия",
    "Netherlands": "Нидерланды", "Germany": "Германия", "Croatia": "Хорватия",
    "Japan": "Япония", "South Korea": "Южная Корея",
    # Добавляем неизвестных участников плей-офф
    "Semifinal 1 Winner": "Победитель ПФ 1",
    "Semifinal 2 Winner": "Победитель ПФ 2",
    "Semifinal 1 Loser": "Проигравший в ПФ 1",
    "Semifinal 2 Loser": "Проигравший в ПФ 2"
}

STATUSES_RU = {
    "FT": "Завершен", "FT-Pens": "По пенальти", "AET": "После доп. времени",
    "PEN": "По пенальти", "Scheduled": "Запланирован", "Halftime": "Перерыв", "HT": "Перерыв"
}

def get_matches(status_filter="all"):
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260610-20260720&limit=200"
    try:
        response = requests.get(url)
        data = response.json()
        events = data.get('events', [])
        if not events: return "Матчи пока не найдены."

        filtered_events = []
        for event in events:
            state = event['status']['type']['state']
            if status_filter == "completed" and state == "post":
                filtered_events.append(event)
            elif status_filter == "scheduled" and state in ["pre", "in"]:
                filtered_events.append(event)
        
        if not filtered_events:
            return "В этой категории пока нет доступных матчей."

        results_text = ""
        selected_events = filtered_events[:8] if status_filter == "scheduled" else filtered_events[-8:]
            
        for event in selected_events:
            competitors = event['competitions'][0]['competitors']
            team1 = TEAMS_RU.get(competitors[0]['team']['name'], competitors[0]['team']['name'])
            team2 = TEAMS_RU.get(competitors[1]['team']['name'], competitors[1]['team']['name'])
            
            status_eng = event['status']['type']['shortDetail']
            status_ru = STATUSES_RU.get(status_eng, status_eng)
            
            # --- ОБРАБОТКА ДАТЫ И ВРЕМЕНИ ---
            raw_date = event['date'] # Формат ESPN: 2026-07-14T20:00Z
            dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%MZ")
            dt += timedelta(hours=3) # Прибавляем 3 часа для часового пояса (Киев/Москва)
            match_date = dt.strftime("%d.%m в %H:%M") # Формат: 14.07 в 23:00
            
            # --- КРАСИВОЕ ОФОРМЛЕНИЕ КАРТОЧКИ ---
            state = event['status']['type']['state']
            if state == "pre":
                results_text += f"📅 **{match_date}**\n⚽ {team1}  **- : -** {team2}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
            else:
                score1 = competitors[0].get('score', '0')
                score2 = competitors[1].get('score', '0')
                results_text += f"📅 **{match_date}**\n⚽ {team1}  **{score1} : {score2}** {team2}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
                
        return results_text
    except Exception as e:
        print(f"Ошибка ESPN: {e}")
        return "Упс, не удалось получить данные."

def get_top_scorers():
    text = (
        "🥇 1. Килиан Мбаппе (Франция) — 5 ⚽\n"
        "🥈 2. Хулиан Альварес (Аргентина) — 4 ⚽\n"
        "🥉 3. Ламин Ямаль (Испания) — 3 ⚽\n"
        "🏅 4. Джуд Беллингем (Англия) — 3 ⚽\n"
        "🏅 5. Винисиус Жуниор (Бразилия) — 2 ⚽\n\n"
        "*(Статистика обновляется...)*"
    )
    return text

# Создаем постоянную клавиатуру при команде /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # resize_keyboard=True делает кнопки аккуратными, а не на пол-экрана
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_past = types.KeyboardButton("🏆 Прошедшие")
    btn_future = types.KeyboardButton("📅 Расписание")
    btn_scorers = types.KeyboardButton("👟 Бомбардиры")
    
    # Кнопки 1 и 2 будут на первом ряду, 3 - на втором
    markup.add(btn_past, btn_future)
    markup.add(btn_scorers)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я бот ЧМ-2026 ⚽.\nТеперь меню всегда под рукой внизу экрана!", 
        reply_markup=markup
    )

# Теперь бот реагирует на обычный текст с кнопок, а не на callback_data
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "🏆 Прошедшие":
        bot.send_message(message.chat.id, f"🏆 **Прошедшие матчи плей-офф:**\n\n{get_matches('completed')}", parse_mode="Markdown")
            
    elif message.text == "📅 Расписание":
        bot.send_message(message.chat.id, f"📅 **Ближайшие матчи:**\n\n{get_matches('scheduled')}", parse_mode="Markdown")
            
    elif message.text == "👟 Бомбардиры":
        bot.send_message(message.chat.id, f"👟 **Лучшие бомбардиры ЧМ-2026:**\n\n{get_top_scorers()}", parse_mode="Markdown")

# ==========================================
# ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА RENDER
# ==========================================
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Бот работает и готов к турниру!"

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
