import asyncio
from flask import Flask, jsonify, request, render_template
import sqlite3
import requests
import telegram.ext
from telegram import Bot
import tracemalloc
from telegram_integration import send_telegram_message

# Започни со следење на алокацијата на меморија за дебагирање
tracemalloc.start()

# Иницијализација на Flask апликацијата
app = Flask(__name__)

# Патека до базата на податоци
DATABASE = 'users_vouchers.db'

@app.route('/')
def index():
    # Серверирај ја главната HTML страница
    return render_template('index.html')

def get_db_connection():
    # Оствари конекција со базата на податоци и овозможи пристап до редови како речник
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/users', methods=['GET'])
def get_all_users():
    """
    Преземи ги сите корисници од табелата 'user_info' во базата на податоци.
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT * FROM user_info')
        rows = cursor.fetchall()
        conn.close()

        users = [dict(row) for row in rows]  # Преобрази ги податоците во листа од речници
        return jsonify(users)  # Врати ги податоците во JSON формат
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Врати грешка ако нешто тргне наопаку

@app.route('/total_spent/<int:user_id>', methods=['GET'])
def get_total_spent(user_id):
    """
    Преземи го вкупниот трошок на корисникот со даден user_id од табелата 'user_spending'.
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'SELECT SUM(money_spent) AS total_spent FROM user_spending WHERE user_id = ?',
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        # Ако нема податоци за вкупниот трошок, постави го на 0
        total_spent = result['total_spent'] if result['total_spent'] is not None else 0

        # Врати го резултатот во JSON формат
        response = {
            "user_id": user_id,
            "total_spent": total_spent
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Врати грешка ако нешто тргне наопаку

@app.route('/high_spenders', methods=['GET'])
def get_high_spenders():
    """
    Преземи ги сите корисници кои се со висок трошок (high_spenders) од базата на податоци.
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT * FROM high_spenders')
        rows = cursor.fetchall()
        conn.close()

        high_spenders = [dict(row) for row in rows]  # Преобрази ги податоците во листа од речници
        return jsonify(high_spenders)  # Врати ги податоците во JSON формат
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Врати грешка ако нешто тргне наопаку

@app.route('/average_spending_by_age', methods=['GET'])
def average_spending_by_age():
    """
    Преземи просечен трошок на корисниците по старосни групи.
    Испрати ги резултатите преку Telegram.
    """
    try:
        # Дефинирање на старосни групи
        age_groups = [
            {"range": "18-24", "min_age": 18, "max_age": 24},
            {"range": "25-30", "min_age": 25, "max_age": 30},
            {"range": "31-36", "min_age": 31, "max_age": 36},
            {"range": "37-47", "min_age": 37, "max_age": 47},
            {"range": ">47", "min_age": 48, "max_age": None},
        ]

        results = {}  # Празен речник за резултати

        conn = get_db_connection()

        for group in age_groups:
            # За секоја старосна група, изврши соодветен SQL upit
            if group["max_age"] is not None:
                query = '''
                    SELECT AVG(us.money_spent) AS avg_spent
                    FROM user_info ui
                    JOIN user_spending us ON ui.user_id = us.user_id
                    WHERE ui.age BETWEEN ? AND ?
                '''
                params = (group["min_age"], group["max_age"])
            else:
                query = '''
                    SELECT AVG(us.money_spent) AS avg_spent
                    FROM user_info ui
                    JOIN user_spending us ON ui.user_id = us.user_id
                    WHERE ui.age >= ?
                '''
                params = (group["min_age"],)

            cursor = conn.execute(query, params)
            result = cursor.fetchone()

            avg_spent = result["avg_spent"] if result["avg_spent"] is not None else 0
            results[group["range"]] = round(avg_spent, 15)  # Додади го резултатот во речникот

        # Испрати резултати преку Telegram
        message = "Average Spending by Age Groups:\n"
        for age_range, avg_spent in results.items():
            message += f"{age_range}: {avg_spent}\n"

        # Испрати порака до Telegram
        asyncio.run(send_telegram_message(message))

        return jsonify(results)  # Врати ги резултатите во JSON формат

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Врати грешка ако нешто тргне наопаку

@app.route('/write_high_spending_user', methods=['POST'])
def write_high_spending_user():
    """
    Додај или ажурирај корисник во табелата 'high_spenders'.
    Прифаќа JSON тело со 'user_id' и 'total_spending'.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON format."}), 400

        user_id = data.get('user_id')
        total_spending = data.get('total_spending')

        if user_id is None or total_spending is None:
            return jsonify({"error": "Missing 'user_id' or 'total_spending'"}), 400

        if total_spending < 1000:
            return jsonify({"error": "Total spending must be greater than or equal to 1000."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO high_spenders (user_id, total_spending)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET total_spending = excluded.total_spending
        """, (user_id, total_spending))

        conn.commit()
        conn.close()

        return jsonify({"message": "User data recorded successfully."}), 201

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

# Функција за испраќање на порака преку Telegram
async def send_telegram_message(message: str):
    try:
        bot = Bot(token='7629158366:AAF1u_AZahxm3DuCgaUqJRSRAuLzpnQ7MTY')
        await bot.send_message(chat_id='924330214', text=message)
        print('Message sent successfully to Telegram')
    except Exception as e:
        print(f"Error while sending message: {e}")

# Главна функција за стартување на Flask апликацијата
if __name__ == '__main__':
    app.run(debug=True)
