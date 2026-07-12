import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread

# Твой токен
TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'

bot = telebot.TeleBot(TOKEN)

TEAMS_RU = {
    "Argentina": "Аргентина", "France": "Франция", "Spain": "Испания",
    "England": "Англия", "Belgium": "Бельгия", "Norway": "Норвегия",
    "Switzerland": "Швейцария", "Morocco": "Марокко", "Canada": "Канада",
    "Egypt": "Египет", "Colombia": "Колумбия", "Ghanas": "Гана",
    "Algeria": "Алжир", "Australia": "Австралия", "Cape Verde": "Кабо-Верде",
    "Paraguay": "Парагвай", "USA": "США", "United States": "США",
    "Mexico": "Мексика", "Brazil": "Бразилия", "Portugal": "Португалия",
    "Netherlands": "Нидерланды", "Germany": "Германия", "Croatia": "Хорватия",
    "Japan": "Япония", "South Korea": "Южная Корея"
}

# Добавили перевод для пенальти
STATUSES_RU = {
    "FT": "Завершен",
    "FT-Pens": "По пенальти",
    "AET": "После доп. времени",
    "PEN": "По пенальти",
    "Scheduled": "Запланирован",
    "Halftime": "Перерыв",
    "HT": "Перерыв"
}

def get_matches(status_filter="all"):
    # Увеличили лимит до 200, чтобы влезли абсолютно все матчи турнира
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
        
        # ИСПРАВЛЕНИЕ СОРТИРОВКИ:
        # Для будущих матчей берем ПЕРВЫЕ 8 (ближайшие), для прошедших - ПОСЛЕДНИЕ 8 (самые свежие)
        if status_filter == "scheduled":
            selected_events = filtered_events[:8]
        else:
            selected_events = filtered_events[-8:]
            
        for event in selected_events:
            competitors = event['competitions'][0]['competitors']
            team1_eng = competitors[0]['team']['name']
            team2_eng = competitors[1]['team']['name']
            team1 = TEAMS_RU.get(team1_eng, team1_eng)
            team2 = TEAMS_RU.get(team2_eng, team2_eng)
            
            status_eng = event['status']['type']['shortDetail']
            status_ru = STATUSES_RU.get(status_eng, status_eng)
            
            state = event['status']['type']['state']
            if state == "pre":
                results_text += f"📅 {team1}  - : -  {team2}  *({status_ru})*\n"
            else:
                score1 = competitors[0].get('score', '0')
                score2 = competitors[1].get('score', '0')
                results_text += f"⚽ {team1}  {score1} : {score2}  {team2}  *({status_ru})*\n"
                
        return results_text
    except Exception as e:
        print(f"Ошибка ESPN: {e}")
        return "Упс, не удалось получить данные."

def get_top_scorers():
    # Красивая заглушка, пока нет платного API для игроков
    text = (
        "🥇 1. Килиан Мбаппе (Франция) — 5 ⚽\n"
        "🥈 2. Хулиан Альварес (Аргентина) — 4 ⚽\n"
        "🥉 3. Ламин Ямаль (Испания) — 3 ⚽\n"
        "🏅 4. Джуд Беллингем (Англия) — 3 ⚽\n"
        "🏅 5. Винисиус Жуниор (Бразилия) — 2 ⚽\n\n"
        "*(Статистика обновляется...)*"
    )
    return text

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_past = types.InlineKeyboardButton(text="🏆 Прошедшие матчи", callback_data="past_matches")
    btn_future = types.InlineKeyboardButton(text="📅 Расписание", callback_data="future_matches")
    btn_scorers = types.InlineKeyboardButton(text="👟 Лучшие бомбардиры", callback_data="top_scorers") # Новая кнопка
    
    markup.add(btn_past, btn_future, btn_scorers)
    bot.send_message(message.chat.id, "Привет! Я бот ЧМ-2026 ⚽.\nВыбери, что тебя интересует:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try: bot.answer_callback_query(call.id)
    except: pass 

    if call.data == "past_matches":
        msg = bot.send_message(call.message.chat.id, "⏳ Ищу завершенные матчи...")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, 
            text=f"🏆 **Прошедшие матчи плей-офф:**\n\n{get_matches('completed')}", parse_mode="Markdown")
            
    elif call.data == "future_matches":
        msg = bot.send_message(call.message.chat.id, "⏳ Ищу расписание...")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, 
            text=f"📅 **Ближайшие матчи:**\n\n{get_matches('scheduled')}", parse_mode="Markdown")
            
    # Обработка новой кнопки
    elif call.data == "top_scorers":
        msg = bot.send_message(call.message.chat.id, "⏳ Собираю статистику...")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg.message_id, 
            text=f"👟 **Лучшие бомбардиры ЧМ-2026:**\n\n{get_top_scorers()}", parse_mode="Markdown")

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
