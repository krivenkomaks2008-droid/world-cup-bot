import telebot
from telebot import types
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'
FOOTBALL_API_KEY = '99f70f9e8fc24cb19383b53a9f4e2324' 

bot = telebot.TeleBot(TOKEN)

TEAMS_RU = {
    "Argentina": "🇦🇷Аргентина", "🇫🇷France": "🇫🇷Франция", "🇪🇸Spain": "🇪🇸Испания",
    "England": "🏴Англия", "Belgium": "🇧🇪Бельгия", "Norway": "🇳🇴Норвегия",
    "Switzerland": "🇨🇭Швейцария", "Morocco": "🇲🇦Марокко", "Canada": "🇨🇦Канада",
    "Egypt": "🇪🇬Египет", "Colombia": "🇨🇴Колумбия", "Ghana": "🇬🇭Гана",
    "Algeria": "🇩🇿Алжир", "Australia": "🇦🇺Австралия", "Cape Verde": "🇨🇻Кабо-Верде",
    "Paraguay": "🇵🇾Парагвай", "USA": "🇺🇸США", "United States": "🇺🇸США",
    "Mexico": "🇲🇽Мексика", "Brazil": "🇧🇷Бразилия", "Portugal": "🇵🇹Португалия",
    "Netherlands": "🇳🇱Нидерланды", "Germany": "🇩🇪Германия", "Croatia": "🇭🇷Хорватия",
    "Japan": "🇯🇵Япония", "South Korea": "🇰🇷Южная Корея"
}

# Статусы у football-data отличаются от ESPN, обновляем словарь
STATUSES_RU = {
    "FINISHED": "Завершен",
    "IN_PLAY": "Идет сейчас",
    "PAUSED": "Перерыв",
    "SCHEDULED": "Запланирован",
    "TIMED": "Запланирован",
    "PENALTY_SHOOTOUT": "Серия пенальти"
}

def get_matches(status_filter="all"):
    # Код турнира WC - Чемпионат Мира
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'errorCode' in data:
            return f"❌ Ошибка API: {data.get('message', 'Неизвестная ошибка')}"
            
        matches = data.get('matches', [])
        if not matches: return "Матчи пока не найдены."

        filtered_matches = []
        for match in matches:
            status = match['status']
            if status_filter == "completed" and status == "FINISHED":
                filtered_matches.append(match)
            elif status_filter == "scheduled" and status in ["SCHEDULED", "TIMED", "IN_PLAY", "PAUSED"]:
                filtered_matches.append(match)
                
        if not filtered_matches:
            return "В этой категории пока нет доступных матчей."

        results_text = ""
        # Берем последние 8 завершенных или первые 8 будущих
        selected = filtered_matches[:8] if status_filter == "scheduled" else filtered_matches[-8:]
        
        for match in selected:
            # Получаем команды (если команда еще неизвестна, API может не отдать 'name')
            home_eng = match.get('homeTeam', {}).get('name', 'Определяется...')
            away_eng = match.get('awayTeam', {}).get('name', 'Определяется...')
            
            home_team = TEAMS_RU.get(home_eng, home_eng)
            away_team = TEAMS_RU.get(away_eng, away_eng)
            
            status_eng = match['status']
            status_ru = STATUSES_RU.get(status_eng, status_eng)
            
            # Обработка даты (UTC -> Московское/Киевское время +3)
            raw_date = match['utcDate'] 
            dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
            dt += timedelta(hours=3)
            match_date = dt.strftime("%d.%m в %H:%M")
            
            # Сборка красивой карточки
            if status_eng in ["SCHEDULED", "TIMED"]:
                results_text += f"📅 **{match_date}**\n⚽ {home_team}  **- : -** {away_team}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
            else:
                home_score = match['score']['fullTime'].get('home', 0)
                away_score = match['score']['fullTime'].get('away', 0)
                
                # Защита от пустых значений
                if home_score is None: home_score = 0
                if away_score is None: away_score = 0
                
                results_text += f"📅 **{match_date}**\n⚽ {home_team}  **{home_score} : {away_score}** {away_team}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
                
        return results_text
    except Exception as e:
        print(f"Ошибка при запросе матчей: {e}")
        return "Упс, не удалось получить данные."

def get_top_scorers():
    # ❗️ НОВОЕ: Реальный запрос к статистике бомбардиров!
    url = "https://api.football-data.org/v4/competitions/WC/scorers"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'errorCode' in data:
            return f"❌ Ошибка API: {data.get('message', 'Неизвестная ошибка')}"
            
        scorers = data.get('scorers', [])
        if not scorers: return "Пока нет данных о бомбардирах."
        
        text = ""
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
        
        # Берем топ-5 игроков
        for i, scorer in enumerate(scorers[:5]):
            player_name = scorer['player']['name']
            team_eng = scorer['team']['name']
            team_ru = TEAMS_RU.get(team_eng, team_eng)
            goals = scorer['goals']
            
            medal = medals[i] if i < len(medals) else "🏅"
            text += f"{medal} {i+1}. {player_name} ({team_ru}) — **{goals}** ⚽\n"
            
        return text
    except Exception as e:
        print(f"Ошибка при запросе бомбардиров: {e}")
        return "Упс, не удалось получить статистику."


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_past = types.KeyboardButton("🏆 Прошедшие")
    btn_future = types.KeyboardButton("📅 Расписание")
    btn_scorers = types.KeyboardButton("👟 Бомбардиры")
    
    markup.add(btn_past, btn_future)
    markup.add(btn_scorers)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я бот ЧМ-2026 ⚽.\nТеперь мое меню всегда под рукой внизу экрана!", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "🏆 Прошедшие":
        bot.send_message(message.chat.id, f"🏆 **Прошедшие матчи:**\n\n{get_matches('completed')}", parse_mode="Markdown")
            
    elif message.text == "📅 Расписание":
        bot.send_message(message.chat.id, f"📅 **Ближайшие матчи:**\n\n{get_matches('scheduled')}", parse_mode="Markdown")
            
    elif message.text == "👟 Бомбардиры":
        bot.send_message(message.chat.id, f"👟 **Лучшие бомбардиры турнира:**\n\n{get_top_scorers()}", parse_mode="Markdown")

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
