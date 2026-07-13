import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# Твои ключи
TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'
FOOTBALL_API_KEY = '99f70f9e8fc24cb19383b53a9f4e2324' 

bot = telebot.TeleBot(TOKEN)

# Прокачанный словарь со всеми флагами
TEAMS_RU = {
    "Argentina": "🇦🇷 Аргентина", "France": "🇫🇷 Франция", "Spain": "🇪🇸 Испания",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Англия", "Belgium": "🇧🇪 Бельгия", "Norway": "🇳🇴 Норвегия",
    "Switzerland": "🇨🇭 Швейцария", "Morocco": "🇲🇦 Марокко", "Canada": "🇨🇦 Канада",
    "Egypt": "🇪🇬 Египет", "Colombia": "🇨🇴 Колумбия", "Ghana": "🇬🇭 Гана",
    "Algeria": "🇩🇿 Алжир", "Australia": "🇦🇺 Австралия", "Cape Verde": "🇨🇻 Кабо-Верде",
    "Paraguay": "🇵🇾 Парагвай", "USA": "🇺🇸 США", "United States": "🇺🇸 США",
    "Mexico": "🇲🇽 Мексика", "Brazil": "🇧🇷 Бразилия", "Portugal": "🇵🇹 Португалия",
    "Netherlands": "🇳🇱 Нидерланды", "Germany": "🇩🇪 Германия", "Croatia": "🇭🇷 Хорватия",
    "Japan": "🇯🇵 Япония", "South Korea": "🇰🇷 Южная Корея"
}

STATUSES_RU = {
    "FINISHED": "Завершен", "IN_PLAY": "Идет сейчас", "PAUSED": "Перерыв",
    "SCHEDULED": "Запланирован", "TIMED": "Запланирован", "PENALTY_SHOOTOUT": "Серия пенальти"
}

def get_matches(status_filter="all"):
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'errorCode' in data: return f"❌ Ошибка API: {data.get('message', 'Неизвестная ошибка')}"
            
        matches = data.get('matches', [])
        if not matches: return "Матчи пока не найдены."

        filtered_matches = []
        for match in matches:
            status = match['status']
            if status_filter == "completed" and status == "FINISHED":
                filtered_matches.append(match)
            elif status_filter == "scheduled" and status in ["SCHEDULED", "TIMED", "IN_PLAY", "PAUSED"]:
                filtered_matches.append(match)
                
        if not filtered_matches: return "В этой категории пока нет доступных матчей."

        results_text = ""
        selected = filtered_matches[:8] if status_filter == "scheduled" else filtered_matches[-8:]
        
        for match in selected:
            home_eng = match.get('homeTeam', {}).get('name', 'Определяется...')
            away_eng = match.get('awayTeam', {}).get('name', 'Определяется...')
            home_team = TEAMS_RU.get(home_eng, home_eng)
            away_team = TEAMS_RU.get(away_eng, away_eng)
            
            status_eng = match['status']
            status_ru = STATUSES_RU.get(status_eng, status_eng)
            
            raw_date = match['utcDate'] 
            dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
            match_date = dt.strftime("%d.%m в %H:%M")
            
            if status_eng in ["SCHEDULED", "TIMED"]:
                results_text += f"📅 **{match_date}**\n⚽ {home_team}  **- : -** {away_team}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
            else:
                home_score = match['score']['fullTime'].get('home', 0)
                away_score = match['score']['fullTime'].get('away', 0)
                if home_score is None: home_score = 0
                if away_score is None: away_score = 0
                results_text += f"📅 **{match_date}**\n⚽ {home_team}  **{home_score} : {away_score}** {away_team}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
                
        return results_text
    except Exception as e:
        return "Упс, не удалось получить данные."

def get_top_scorers():
    url = "https://api.football-data.org/v4/competitions/WC/scorers"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'errorCode' in data: return f"❌ Ошибка API: {data.get('message', 'Неизвестная ошибка')}"
            
        scorers = data.get('scorers', [])
        if not scorers: return "Пока нет данных о бомбардирах."
        
        text = ""
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
        
        for i, scorer in enumerate(scorers[:5]):
            player_name = scorer['player']['name']
            team_eng = scorer['team']['name']
            team_ru = TEAMS_RU.get(team_eng, team_eng)
            goals = scorer['goals']
            
            medal = medals[i] if i < len(medals) else "🏅"
            text += f"{medal} {i+1}. {player_name} ({team_ru}) — **{goals}** ⚽\n"
            
        return text
    except Exception as e:
        return "Упс, не удалось получить статистику."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🏆 Прошедшие"), types.KeyboardButton("📅 Расписание"))
    markup.add(types.KeyboardButton("👟 Бомбардиры"))
    
     bot.send_message(message.chat.id, "Привет! Я бот ЧМ-2026 ⚽.\nМеню внизу экрана, а также слева в кнопке ☰. " \
    "Жми на кнопку, чтобы выбрать действие.", reply_markup=markup)

# ---  Обработчик системных команд ---
@bot.message_handler(commands=['past', 'future', 'scorers'])
def handle_commands(message):
    if message.text == '/past':
        bot.send_message(message.chat.id, f"🏆 **Прошедшие матчи:**\n\n{get_matches('completed')}", parse_mode="Markdown")
    elif message.text == '/future':
        bot.send_message(message.chat.id, f"📅 **Ближайшие матчи:**\n\n{get_matches('scheduled')}", parse_mode="Markdown")
    elif message.text == '/scorers':
        bot.send_message(message.chat.id, f"👟 **Лучшие бомбардиры:**\n\n{get_top_scorers()}", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "🏆 Прошедшие":
        bot.send_message(message.chat.id, f"🏆 **Прошедшие матчи:**\n\n{get_matches('completed')}", parse_mode="Markdown")
    elif message.text == "📅 Расписание":
        bot.send_message(message.chat.id, f"📅 **Ближайшие матчи:**\n\n{get_matches('scheduled')}", parse_mode="Markdown")
    elif message.text == "👟 Бомбардиры":
        bot.send_message(message.chat.id, f"👟 **Лучшие бомбардиры:**\n\n{get_top_scorers()}", parse_mode="Markdown")

# ==========================================
# ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА RENDER
# ==========================================
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Бот работает!"
def run_bot(): bot.polling(none_stop=True)
if __name__ == '__main__':
    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
