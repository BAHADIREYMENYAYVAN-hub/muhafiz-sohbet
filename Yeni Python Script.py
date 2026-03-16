import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'muhafiz_gizli_sifre_2026'
app.config['UPLOAD_FOLDER'] = 'uploads'
# Render'da her şeyin doğru çalışması için async_mode ekledik
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- 1. KULLANICI LİSTESİ ---
users = {
    "BAHADIR": "3648",
    "BIDIK": "2392",
    "Yetiş": "1234",
    "Bayvampir": "1235"  # Yazım hatası düzeltildi!
}

# Klasör ve Veritabanı Hazırlığı
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def veritabani_hazirla():
    conn = sqlite3.connect('sohbet.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesajlar (name TEXT, msg TEXT)''')
    conn.commit()
    conn.close()

# --- 2. BOT CEVAP SİSTEMİ ---
def bot_cevap_ver(mesaj, user):
    m = mesaj.lower()
    if "selam" in m: 
        return f"Selam {user}! Tevhit Muhafızları emrinde. Gruptaki herkes aktif mi?"
    if "muhafız" in m: 
        return "Sistemi ve grubu koruyorum. Tüm veri akışı şifreli!"
    return None

# --- 3. SAYFA YÖNLENDİRMELERİ ---
@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    # Eski mesajları çek
    conn = sqlite3.connect('sohbet.db')
    c = conn.cursor()
    c.execute("SELECT name, msg FROM mesajlar")
    eski_mesajlar = [{'name': row[0], 'msg': row[1]} for row in c.fetchall()]
    conn.close()
    return render_template('index.html', username=session.get('username'), eski_mesajlar=eski_mesajlar)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('username')
    pw = request.form.get('password')
    if user in users and users[user] == pw:
        session['logged_in'] = True
        session['username'] = user
        return redirect(url_for('index'))
    return "Hatalı giriş! <a href='/'>Geri dön</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- 4. DOSYA GÖNDERME ---
@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'): return 'Yetkisiz', 401
    file = request.files['file']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        msg_data = {'name': 'Sistem', 'msg': f'📁 {session.get("username")} bir dosya gönderdi: <a href="/files/{file.filename}" target="_blank">{file.filename}</a>'}
        # Dosya mesajını da kaydet
        conn = sqlite3.connect('sohbet.db')
        c = conn.cursor()
        c.execute("INSERT INTO mesajlar (name, msg) VALUES (?, ?)", (msg_data['name'], msg_data['msg']))
        conn.commit()
        conn.close()
        socketio.emit('message', msg_data)
    return 'OK', 200

@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- 5. MESAJLAŞMA ---
@socketio.on('message')
def handle_message(data):
    # Mesajı veritabanına kaydet (Kalıcı olması için)
    conn = sqlite3.connect('sohbet.db')
    c = conn.cursor()
    c.execute("INSERT INTO mesajlar (name, msg) VALUES (?, ?)", (data['name'], data['msg']))
    conn.commit()
    conn.close()
    
    emit('message', data, broadcast=True)
    
    cevap = bot_cevap_ver(data['msg'], data['name'])
    if cevap:
        bot_data = {'name': '🛡️ Muhafız', 'msg': cevap}
        # Botun cevabını da kaydet
        conn = sqlite3.connect('sohbet.db')
        c = conn.cursor()
        c.execute("INSERT INTO mesajlar (name, msg) VALUES (?, ?)", (bot_data['name'], bot_data['msg']))
        conn.commit()
        conn.close()
        emit('message', bot_data, broadcast=True)

if __name__ == "__main__":
    veritabani_hazirla()
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
