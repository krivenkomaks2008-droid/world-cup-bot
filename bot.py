import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread

# 1. ТВОЙ ТОКЕН ОТ BOTFATHER
TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'

bot = telebot.TeleBot(TOKEN)

TEAMS_RU = {
    "Argentina": "Аргентина", "France": "Франция", "Spain": "Испания",
    "England": "Англия", "Belgium": "Бельгия", "Norway": "Норвегия",
    "Switzerland": "Швейцария", "Morocco": "Марокко", "Canada": "Канада",
    "Egypt": "Египет", "Colombia": "Колумбия", "Ghanas": "Гана",
    "Algeria": "Алжир", "Australia": "Австралия", "Cape Verde": "Кабо-Верде",
    "Paraguay": "Парагвай", "USA": "США", "United States": "США",
    "Mexico": "Мексика", "Brazil": "Бразилия", "Portugal": "Португалия"
}

def get_football_results():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    try:
        response = requests.get(url)
        data = response.json()
        events = data.get('events', [])
        if not events: return "Матчи пока не найдены."

        results_text = ""
        for event in events[-5:]:
            competitors = event['competitions'][0]['competitors']
            team1_eng = competitors[0]['team']['name']
            score1 = competitors[0].get('score', '-')
            team2_eng = competitors[1]['team']['name']
            score2 = competitors[1].get('score', '-')
            
            team1 = TEAMS_RU.get(team1_eng, team1_eng)
            team2 = TEAMS_RU.get(team2_eng, team2_eng)
            
            status = event['status']['type']['shortDetail']
            if status == "FT": status = "Завершен"
            
            results_text += f"⚽ {team1} {score1} : {score2} {team2} *({status})*\n"
        return results_text
    except Exception as e:
        print(f"Ошибка ESPN: {e}")
        return "Упс, не удалось получить данные."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="🏆 Узнать результаты", callback_data="get_results"))
    bot.send_message(message.chat.id, "Привет! Я бот ЧМ-2026 ⚽.\nЖми на кнопку!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "get_results":
        try: bot.answer_callback_query(call.id)
        except: pass 
        msg = bot.send_message(call.message.chat.id, "⏳ Спрашиваю у ESPN...")
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=msg.message_id, 
            text=f"🏆 **Свежие матчи:**\n\n{get_football_results()}", parse_mode="Markdown"
        )

# ==========================================
# 2. ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА RENDER
# ==========================================
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Бот работает и готов к турниру!"

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Запускаем бота в отдельном фоновом потоке
    Thread(target=run_bot).start()
    
    # Запускаем веб-сервер, чтобы Render был доволен
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)