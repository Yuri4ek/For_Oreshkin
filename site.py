from flask import Flask, render_template, request, jsonify
import sqlite3

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
            "INSERT INTO repairs (device_type, issue_description, client_name, repairer_name, request_date) VALUES (?, ?, ?, ?, ?)",
            (data.get('type', ''),
             data.get('description', ''),
             data.get('user', ''),
             data.get('repairer_name', ''),
             data.get('time', ''))
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
            {"id": r[0], "device_type": r[1], "issue_description": r[2],
             "client_name": r[3], "repairer_name": r[4], "request_date": r[5]}
            for r in rows
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
            device_type TEXT,
            issue_description TEXT,
            client_name TEXT,
            repairer_name TEXT,
            request_date DATE
        )
    """)
    conn.commit()
    conn.close()
    # Для хостинга используйте WSGI-сервер, например, gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 site:app
    app.run(host='0.0.0.0', port=5000, debug=True)