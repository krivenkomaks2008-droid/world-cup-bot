import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread

# 1. ТВОЙ ТОКЕН ОТ BOTFATHER
TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'

bot = telebot.TeleBot(TOKEN)

# Переводчик стран
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

# Переводчик статусов матча
STATUSES_RU = {
    "FT": "Завершен",
    "AET": "После доп. времени",
    "PEN": "По пенальти",
    "Scheduled": "Запланирован",
    "Halftime": "Перерыв",
    "HT": "Перерыв"
}

# Единая функция, которая умеет фильтровать матчи
def get_matches(status_filter="all"):
    # Добавили параметры dates (весь период турнира) и limit=100
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260610-20260720&limit=100"
    
    try:
        response = requests.get(url)
        data = response.json()
        events = data.get('events', [])
        
        if not events: 
            return "Матчи пока не найдены."

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
        # Берем 8 последних матчей
        for event in filtered_events[-8:]:
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

# Команда /start с двумя кнопками
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # row_width=1 выстроит кнопки друг под другом в один столбик
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_past = types.InlineKeyboardButton(text="🏆 Прошедшие матчи", callback_data="past_matches")
    btn_future = types.InlineKeyboardButton(text="📅 Расписание (Будущие)", callback_data="future_matches")
    
    markup.add(btn_past, btn_future)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я бот ЧМ-2026 ⚽.\nВыбери, что тебя интересует:", 
        reply_markup=markup
    )

# Обработчик нажатий
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try: bot.answer_callback_query(call.id)
    except: pass 

    # Если нажали первую кнопку
    if call.data == "past_matches":
        msg = bot.send_message(call.message.chat.id, "⏳ Ищу завершенные матчи...")
        results_text = get_matches(status_filter="completed")
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=msg.message_id, 
            text=f"🏆 **Прошедшие матчи плей-офф:**\n\n{results_text}", parse_mode="Markdown"
        )
        
    # Если нажали вторую кнопку
    elif call.data == "future_matches":
        msg = bot.send_message(call.message.chat.id, "⏳ Ищу расписание...")
        results_text = get_matches(status_filter="scheduled")
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=msg.message_id, 
            text=f"📅 **Ближайшие матчи:**\n\n{results_text}", parse_mode="Markdown"
        )

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
