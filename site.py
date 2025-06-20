from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
@app.route('/index')
def display():
    return render_template('index.html')


@app.route('/reviews')
def reviews():
    return render_template('reviews.html')


@app.route('/receive', methods=['POST'])
def receive_data():
    data = request.get_json()
    try:
        conn = sqlite3.connect('repairs.db')
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO repairs (
                client_name, device_type, manufacturer, model, serial_number, 
                accessories, client_address, status, status_timestamp, issue_description, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get('client_name', ''),
                data.get('device_type', ''),
                data.get('manufacturer', ''),
                data.get('model', ''),
                data.get('serial_number', ''),
                data.get('accessories', ''),
                data.get('client_address', ''),
                data.get('status', 'принят'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('issue_description', ''),
                data.get('notes', '')
            )
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_repairs', methods=['GET'])
def get_repairs():
    try:
        conn = sqlite3.connect('repairs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repairs")
        rows = cursor.fetchall()
        repairs = [
            {
                "id": r[0],
                "client_name": r[1],
                "device_type": r[2],
                "manufacturer": r[3],
                "model": r[4],
                "serial_number": r[5],
                "accessories": r[6],
                "client_address": r[7],
                "status": r[8],
                "status_timestamp": r[9],
                "issue_description": r[10],
                "notes": r[11]
            } for r in rows
        ]
        conn.close()
        return jsonify(repairs), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/delete_repair/<int:record_id>', methods=['DELETE'])
def delete_repair(record_id):
    try:
        conn = sqlite3.connect('repairs.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repairs WHERE id=?", (record_id,))
        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Запись не найдена"}), 404
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/delete_all_repairs', methods=['DELETE'])
def delete_all_repairs():
    try:
        conn = sqlite3.connect('repairs.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repairs")
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    conn = sqlite3.connect('repairs.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY,
            client_name TEXT,
            device_type TEXT,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            accessories TEXT,
            client_address TEXT,
            status TEXT,
            status_timestamp TEXT,
            issue_description TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()
    # Для хостинга используйте WSGI-сервер, например, gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 site:app
    app.run(host='0.0.0.0', port=5000, debug=True)
