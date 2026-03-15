import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'muhafiz_gizli_sifre_2026'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app)

# --- KULLANICI LİSTESİ (Arkadaşlarını buraya ekle) ---
# Format: "kullanıcı_adı": "şifre"
users = {
    "BAHADIR": "3648",
    "BIDIK": "2392",
    "Yetiş": "1234",
    "Salih": "2222"
}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def bot_cevap_ver(mesaj, user):
    m = mesaj.lower()
    if "selam" in m: 
        return f"Selam {user}! Tevhit Muhafızları emrinde. Gruptaki herkes aktif mi?"
    if "muhafız" in m: 
        return "Sistemi ve grubu koruyorum. Tüm veri akışı şifreli!"
    return None

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('index.html', username=session.get('username'))

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

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'): return 'Yetkisiz', 401
    file = request.files['file']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        socketio.emit('message', {'name': 'Sistem', 'msg': f'📁 {session.get("username")} bir dosya gönderdi: <a href="/files/{file.filename}" target="_blank">{file.filename}</a>'})
    return 'OK', 200

@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('message')
def handle_message(data):
    # Mesajı gruptaki HERKESE gönder
    emit('message', data, broadcast=True)
    
    # Botun cevabını kontrol et
    cevap = bot_cevap_ver(data['msg'], data['name'])
    if cevap:
        emit('message', {'name': '🛡️ Muhafız', 'msg': cevap}, broadcast=True)

if __name__ == "__main__":
    # Render'ın verdiği portu otomatik bulur
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
