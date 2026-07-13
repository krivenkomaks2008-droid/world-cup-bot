import telebot
from telebot import types
import requests
import os
import random
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

TOKEN = '8851681234:AAGbJb_1-GTnCkHyGInK9lnAAZj4MSKsk-s'
FOOTBALL_API_KEY = '99f70f9e8fc24cb19383b53a9f4e2324' 

bot = telebot.TeleBot(TOKEN)

TEAMS_RU = {
    "Argentina": "🇦🇷 Аргентина", "France": "🇫🇷 Франция", "Spain": "🇪🇸 Испания",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Англия", "Belgium": "🇧🇪 Бельгия", "Norway": "🇳🇴 Норвегия",
    "Switzerland": "🇨🇭 Швейцария", "Morocco": "🇲🇦 Марокко", "Canada": "🇨🇦 Канада",
    "Egypt": "🇪🇬 Египет", "Colombia": "🇨🇴 Колумбия", "Ghana": "🇬🇭 Гана",
    "Algeria": "🇩🇿 Алжир", "Australia": "🇦🇺 Австралия", "Cape Verde": "🇨🇻 Кабо-Верде",
    "Paraguay": "🇵🇾 Парагвай", "USA": "🇺🇸 США", "United States": "🇺🇸 США",
    "Mexico": "🇲🇽 Мексика", "Brazil": "🇧🇷 Бразилия", "Portugal": "🇵🇹 Португалия",
    "Netherlands": "🇳🇱 Нидерланды", "Germany": "🇩🇪 Германия", "Croatia": "🇭🇷 Хорватия",
    "Japan": "🇯🇵 Япония", "South Korea": "🇰🇷 Южная Корея",
    "Semifinal 1 Winner": "Победитель ПФ 1", "Semifinal 2 Winner": "Победитель ПФ 2",
    "Semifinal 1 Loser": "Проигравший в ПФ 1", "Semifinal 2 Loser": "Проигравший в ПФ 2"
}

STATUSES_RU = {
    "FINISHED": "Завершен", "IN_PLAY": "Идет сейчас", "PAUSED": "Перерыв",
    "SCHEDULED": "Запланирован", "TIMED": "Запланирован", "PENALTY_SHOOTOUT": "Пенальти"
}

# Наш рейтинг силы команд
TEAM_POWER = {
    "🇦🇷 Аргентина": 96, "🇫🇷 Франция": 95, "🇪🇸 Испания": 94, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Англия": 93,
    "🇧🇷 Бразилия": 94, "🇩🇪 Германия": 90, "🇵🇹 Португалия": 91, "🇧🇪 Бельгия": 88,
    "🇳🇱 Нидерланды": 89, "🇨🇭 Швейцария": 82, "🇲🇦 Марокко": 83, "🇭🇷 Хорватия": 85
}

# --- ФУНКЦИИ ДЛЯ КЛАВИАТУР ---

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏆 Прошедшие матчи", callback_data="past"),
        types.InlineKeyboardButton("📅 Расписание матчей", callback_data="future"),
        types.InlineKeyboardButton("🔮 AI-Симуляция тура", callback_data="predictions"),
        types.InlineKeyboardButton("👟 Лучшие бомбардиры", callback_data="scorers")
    )
    return markup

def get_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu"))
    return markup

# --- НОВАЯ ФУНКЦИЯ: СИМУЛЯТОР МАТЧА ---

def simulate_match(home_team, away_team, p1, p2):
    diff = p1 - p2
    
    # Симуляция 90 минут (от 0 до 3 голов, сдвиг зависит от разницы в силе)
    goals_1 = max(0, random.randint(0, 3) + (1 if diff > 4 else 0))
    goals_2 = max(0, random.randint(0, 3) + (1 if diff < -4 else 0))
    
    if goals_1 > goals_2:
        return f"**{goals_1} : {goals_2}** (Проход {home_team})"
    elif goals_2 > goals_1:
        return f"**{goals_1} : {goals_2}** (Проход {away_team})"
    else:
        # Ничья -> Симуляция дополнительного времени
        et_1 = random.randint(0, 1)
        et_2 = random.randint(0, 1)
        
        final_1 = goals_1 + et_1
        final_2 = goals_2 + et_2
        
        if final_1 > final_2:
            return f"**{final_1} : {final_2}** (В доп. время проходит {home_team})"
        elif final_2 > final_1:
            return f"**{final_1} : {final_2}** (В доп. время проходит {away_team})"
        else:
            # Снова ничья -> Серия пенальти (шансы 50/50)
            winner = home_team if random.choice([True, False]) else away_team
            return f"**{final_1} : {final_2}** (По пенальти проходит {winner})"

# --- ФУНКЦИИ ПОЛУЧЕНИЯ ДАННЫХ ---

def get_matches(status_filter="all", is_prediction=False):
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if 'errorCode' in data: return "❌ Ошибка API."
            
        matches = data.get('matches', [])
        if not matches: return "Матчи пока не найдены."

        filtered_matches = [m for m in matches if (status_filter == "completed" and m['status'] == "FINISHED") or (status_filter == "scheduled" and m['status'] in ["SCHEDULED", "TIMED", "IN_PLAY"])]
        if not filtered_matches: return "В этой категории пока нет матчей."

        results_text = ""
        selected = filtered_matches[:5] if status_filter == "scheduled" else filtered_matches[-5:]
        
        for match in selected:
            # Более надежная проверка на пустоту от API
            home_eng = match.get('homeTeam', {}).get('name')
            away_eng = match.get('awayTeam', {}).get('name')
            
            if not home_eng: home_eng = 'Определяется...'
            if not away_eng: away_eng = 'Определяется...'
            
            home = TEAMS_RU.get(home_eng, home_eng)
            away = TEAMS_RU.get(away_eng, away_eng)
            
            dt = datetime.strptime(match['utcDate'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
            date_str = dt.strftime("%d.%m в %H:%M")
            
            if is_prediction and status_filter == "scheduled":
                # ❗️ Защита от вангования на неизвестных командах
                if home == 'Определяется...' or away == 'Определяется...':
                    prediction_result = "⏳ _Команды еще не определены_"
                else:
                    p1 = TEAM_POWER.get(home, 75)
                    p2 = TEAM_POWER.get(away, 75)
                    prediction_result = simulate_match(home, away, p1, p2)
                
                results_text += f"📅 **{date_str}**\n⚔️ {home} vs {away}\n🔮 Прогноз: {prediction_result}\n━━━━━━━━━━━━━━━━━━\n"
            
            else:
                status_ru = STATUSES_RU.get(match['status'], match['status'])
                if match['status'] in ["SCHEDULED", "TIMED"]:
                    results_text += f"📅 **{date_str}**\n⚽ {home}  **- : -** {away}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
                else:
                    h_score = match['score']['fullTime'].get('home', 0)
                    a_score = match['score']['fullTime'].get('away', 0)
                    results_text += f"📅 **{date_str}**\n⚽ {home}  **{h_score or 0} : {a_score or 0}** {away}\n_{status_ru}_\n━━━━━━━━━━━━━━━━━━\n"
                
        return results_text
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Упс, не удалось получить данные."

def get_top_scorers():
    url = "https://api.football-data.org/v4/competitions/WC/scorers"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        data = requests.get(url, headers=headers).json()
        if 'errorCode' in data: return "❌ Ошибка API."
        scorers = data.get('scorers', [])
        if not scorers: return "Нет данных о бомбардирах."
        
        text = ""
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
        for i, scorer in enumerate(scorers[:5]):
            name = scorer['player']['name']
            team = TEAMS_RU.get(scorer['team']['name'], scorer['team']['name'])
            text += f"{medals[i]} {i+1}. {name} ({team}) — **{scorer['goals']}** ⚽\n"
        return text
    except Exception:
        return "Упс, не удалось получить статистику."

# --- ОБРАБОТЧИКИ ТЕЛЕГРАМ ---

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    # 1. Создаем команду для удаления старой нижней клавиатуры
    remove_keyboard = types.ReplyKeyboardRemove()
    
    # 2. Отправляем техническое сообщение, которое сотрет старые кнопки
    msg = bot.send_message(
        message.chat.id, 
        "⏳ Загрузка интерфейса...", 
        reply_markup=remove_keyboard
    )
    
    # 3. Сразу же удаляем это техническое сообщение, чтобы не мусорить в чате
    bot.delete_message(message.chat.id, msg.message_id)

    # 4. Отправляем наше нормальное меню с новыми прозрачными кнопками
    bot.send_message(
        message.chat.id, 
        "Привет! Я бот ЧМ-2026 ⚽.\nВыбери нужный раздел в меню ниже:", 
        reply_markup=get_main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try: bot.answer_callback_query(call.id)
    except: pass 

    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if call.data == "main_menu":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
            text="Главное меню ⚽. Что тебя интересует?", reply_markup=get_main_menu())

    elif call.data == "past":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
            text=f"🏆 **Прошедшие матчи:**\n\n{get_matches('completed')}", 
            parse_mode="Markdown", reply_markup=get_back_button())
            
    elif call.data == "future":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
            text=f"📅 **Ближайшие матчи:**\n\n{get_matches('scheduled')}", 
            parse_mode="Markdown", reply_markup=get_back_button())
            
    elif call.data == "predictions":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
            text=f"🔮 **AI-Симуляция тура:**\n\n{get_matches('scheduled', is_prediction=True)}", 
            parse_mode="Markdown", reply_markup=get_back_button())
            
    elif call.data == "scorers":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
            text=f"👟 **Лучшие бомбардиры:**\n\n{get_top_scorers()}", 
            parse_mode="Markdown", reply_markup=get_back_button())

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
