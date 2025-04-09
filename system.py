from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import sqlite3
import requests
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database initialization
def init_db():
    conn = sqlite3.connect('learning.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                 name TEXT, 
                 learning_style TEXT, 
                 knowledge_level INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS materials
                 (id INTEGER PRIMARY KEY,
                 topic TEXT,
                 content TEXT,
                 difficulty INTEGER,
                 source TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS schedule
                 (user_id INTEGER,
                 material_id INTEGER,
                 next_review DATE,
                 interval INTEGER,
                 ease_factor REAL,
                 FOREIGN KEY(user_id) REFERENCES users(id),
                 FOREIGN KEY(material_id) REFERENCES materials(id))''')
    
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.after_request
def enforce_json(response):
    """Ensure all API responses are JSON"""
    if request.path.startswith('/api'):
        if response.content_type != 'application/json':
            response = make_response(jsonify({
                "error": "Invalid response format",
                "received": str(response.data)[:100]
            }), 500)
            response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/user_profile', methods=['POST'])
def user_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        required = ['name', 'learning_style', 'knowledge_level']
        if not all(k in data for k in required):
            return jsonify({"error": f"Missing fields. Required: {required}"}), 400

        conn = sqlite3.connect('learning.db')
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM users WHERE id=?', (1,))
        if c.fetchone():
            c.execute('''UPDATE users SET 
                       name=?, learning_style=?, knowledge_level=?
                       WHERE id=?''',
                    (data['name'], data['learning_style'], data['knowledge_level'], 1))
        else:
            c.execute('''INSERT INTO users 
                       (id, name, learning_style, knowledge_level)
                       VALUES (?, ?, ?, ?)''',
                    (1, data['name'], data['learning_style'], data['knowledge_level']))
        
        conn.commit()
        return jsonify({"status": "success"})
        
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/learn', methods=['POST'])
def learn():
    try:
        data = request.get_json()
        if not data or 'topic' not in data:
            return jsonify({"error": "Topic is required"}), 400

        content = fetch_wikipedia_content(data['topic'])
        if not content:
            return jsonify({"error": "Content not found"}), 404
            
        return jsonify(content)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_material', methods=['POST'])
def save_material():
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['topic', 'content']):
            return jsonify({"error": "Topic and content are required"}), 400

        conn = sqlite3.connect('learning.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO materials (topic, content, difficulty, source)
                   VALUES (?, ?, ?, ?)''',
                (data['topic'], data['content'], 2, 'user'))
        
        material_id = c.lastrowid
        
        c.execute('''INSERT INTO schedule 
                   (user_id, material_id, next_review, interval, ease_factor)
                   VALUES (?, ?, ?, ?, ?)''',
                (1, material_id, datetime.now(), 0, 2.5))
        
        conn.commit()
        return jsonify({"status": "success", "material_id": material_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/get_reviews', methods=['GET'])
def get_reviews():
    try:
        conn = sqlite3.connect('learning.db')
        c = conn.cursor()
        
        c.execute('''SELECT m.id, m.topic, m.content, s.next_review 
                   FROM materials m
                   JOIN schedule s ON m.id = s.material_id
                   WHERE s.user_id = 1 AND s.next_review <= ?''',
                (datetime.now(),))
        
        reviews = [{
            'id': row[0],
            'topic': row[1],
            'content': row[2],
            'next_review': row[3].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[3], datetime) else row[3]
        } for row in c.fetchall()]
        
        return jsonify(reviews)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/review', methods=['POST'])
def review():
    try:
        data = request.get_json()
        if not data or 'material_id' not in data or 'performance' not in data:
            return jsonify({"error": "Material ID and performance rating required"}), 400

        conn = sqlite3.connect('learning.db')
        c = conn.cursor()
        
        c.execute('''SELECT interval, ease_factor FROM schedule
                   WHERE user_id=? AND material_id=?''',
                (1, data['material_id']))
        row = c.fetchone()
        current_interval, current_ease = row if row else (0, 2.5)
        
        new_interval, new_ease = calculate_spaced_repetition(
            data['performance'], current_interval, current_ease)
        
        next_review = datetime.now() + timedelta(days=new_interval)
        c.execute('''UPDATE schedule SET
                   next_review=?,
                   interval=?,
                   ease_factor=?
                   WHERE user_id=? AND material_id=?''',
                (next_review, new_interval, new_ease, 1, data['material_id']))
        
        conn.commit()
        return jsonify({
            'next_review': next_review.strftime('%Y-%m-%d %H:%M:%S'),
            'interval_days': new_interval,
            'ease_factor': new_ease
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

def fetch_wikipedia_content(topic):
    endpoint = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    try:
        response = requests.get(endpoint + topic, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'title': data.get('title', topic),
            'content': data.get('extract', 'No content available'),
            'source': 'Wikipedia',
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
        }
    except Exception:
        return None

def calculate_spaced_repetition(performance_rating, current_interval, current_ease):
    if performance_rating >= 3:
        if current_interval == 0:
            new_interval = 1
        elif current_interval == 1:
            new_interval = 3
        else:
            new_interval = round(current_interval * current_ease)
        new_ease = max(1.3, current_ease + 0.1 - (5 - performance_rating) * 0.08)
    else:
        new_interval = 0
        new_ease = max(1.3, current_ease - 0.2)
    
    return new_interval, new_ease

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)