# 🎥 Видеочат - Полная инструкция по запуску

## 📦 Файлы для создания

### 1. `app.py` - основной файл
```python
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25
)

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    join_room(room)
    
    if room not in rooms:
        rooms[room] = {}
    rooms[room][request.sid] = username
    
    emit('user_joined', {
        'userId': request.sid,
        'username': username,
        'users': len(rooms[room])
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    if room in rooms and request.sid in rooms[room]:
        username = rooms[room][request.sid]
        del rooms[room][request.sid]
        leave_room(room)
        emit('user_left', {
            'userId': request.sid,
            'username': username,
            'users': len(rooms[room])
        }, room=room)
        if len(rooms[room]) == 0:
            del rooms[room]

@socketio.on('offer')
def on_offer(data):
    emit('offer', {'from': request.sid, 'offer': data['offer']}, room=data['to'])

@socketio.on('answer')
def on_answer(data):
    emit('answer', {'from': request.sid, 'answer': data['answer']}, room=data['to'])

@socketio.on('ice_candidate')
def on_ice_candidate(data):
    emit('ice_candidate', {'from': request.sid, 'candidate': data['candidate']}, room=data['to'])

@socketio.on('disconnect')
def on_disconnect():
    for room in list(rooms.keys()):
        if request.sid in rooms[room]:
            username = rooms[room][request.sid]
            del rooms[room][request.sid]
            emit('user_left', {
                'userId': request.sid,
                'username': username,
                'users': len(rooms[room])
            }, room=room)
            if len(rooms[room]) == 0:
                del rooms[room]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
```

### 2. `templates/index.html` - интерфейс
Создайте папку `templates` и файл `index.html` внутри:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Видеочат</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
        }
        .setup, .chat { display: none; }
        .setup.active, .chat.active { display: block; }
        
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #5568d3; }
        
        .info-panel {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .share-box {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 2px dashed #667eea;
        }
        .share-link {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .share-link input { flex: 1; }
        
        .videos {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .video-box {
            position: relative;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            aspect-ratio: 16/9;
        }
        video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .video-label {
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        
        .controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn-control {
            padding: 15px 25px;
            border-radius: 50px;
            font-weight: 600;
        }
        .btn-danger {
            background: #e74c3c;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        
        .status {
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .status.warning { background: #fff3cd; color: #856404; }
        
        @media (max-width: 768px) {
            .videos { grid-template-columns: 1fr; }
            .controls { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Защищенный Видеочат</h1>
        
        <!-- Экран входа -->
        <div class="setup active">
            <div class="form-group">
                <label>👤 Ваше имя:</label>
                <input type="text" id="username" placeholder="Введите имя">
            </div>
            <div class="form-group">
                <label>🚪 ID комнаты:</label>
                <input type="text" id="roomId" placeholder="Оставьте пустым для новой комнаты">
            </div>
            <div class="form-group">
                <label>🔐 Ключ шифрования:</label>
                <input type="password" id="encKey" placeholder="Оставьте пустым для авто-генерации">
            </div>
            <div style="text-align: center;">
                <button onclick="join()" style="padding: 15px 40px; font-size: 18px;">Войти</button>
            </div>
            <div id="setupMsg"></div>
        </div>
        
        <!-- Экран чата -->
        <div class="chat">
            <div class="info-panel">
                <div><strong>Комната:</strong> <span id="roomInfo"></span></div>
                <div><strong>Участников:</strong> <span id="userCount">1</span></div>
            </div>
            
            <div class="share-box">
                <strong>🔗 Пригласить друзей:</strong>
                <div class="share-link">
                    <input type="text" id="shareUrl" readonly>
                    <button onclick="copy()">📋 Копировать</button>
                </div>
                <small style="color: #666;">⚠️ Передайте ключ шифрования отдельно!</small>
            </div>
            
            <div id="chatMsg"></div>
            
            <div class="videos">
                <div class="video-box">
                    <video id="local" autoplay muted playsinline></video>
                    <div class="video-label">Вы</div>
                </div>
                <div id="remote"></div>
            </div>
            
            <div class="controls">
                <button class="btn-control" id="videoBtn" onclick="toggleVideo()">📹 Камера ВКЛ</button>
                <button class="btn-control" id="audioBtn" onclick="toggleAudio()">🎤 Микрофон ВКЛ</button>
                <button class="btn-control btn-danger" onclick="leave()">❌ Выйти</button>
            </div>
        </div>
    </div>

    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        let stream, peers = {}, room, user, key;
        let videoOn = true, audioOn = true;

        const cfg = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };

        function encrypt(txt, k) {
            if (!k) return txt;
            let r = '';
            for (let i = 0; i < txt.length; i++) {
                r += String.fromCharCode(txt.charCodeAt(i) ^ k.charCodeAt(i % k.length));
            }
            return btoa(r);
        }

        function decrypt(enc, k) {
            if (!k) return enc;
            try {
                const txt = atob(enc);
                let r = '';
                for (let i = 0; i < txt.length; i++) {
                    r += String.fromCharCode(txt.charCodeAt(i) ^ k.charCodeAt(i % k.length));
                }
                return r;
            } catch (e) {
                return enc;
            }
        }

        async function join() {
            user = document.getElementById('username').value.trim();
            room = document.getElementById('roomId').value.trim() || Math.random().toString(36).substr(2, 9);
            key = document.getElementById('encKey').value || Math.random().toString(36).substr(2, 16);

            if (!user) {
                msg('setupMsg', 'Введите имя!', 'error');
                return;
            }

            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                    audio: { echoCancellation: true, noiseSuppression: true }
                });

                document.getElementById('local').srcObject = stream;
                document.querySelector('.setup').classList.remove('active');
                document.querySelector('.chat').classList.add('active');
                document.getElementById('roomInfo').textContent = room;
                document.getElementById('shareUrl').value = `${window.location.origin}/?room=${room}`;

                socket.emit('join', { room, username: user });
                msg('chatMsg', 'Подключено!', 'success');
            } catch (e) {
                msg('setupMsg', 'Ошибка доступа к камере/микрофону', 'error');
            }
        }

        window.onload = () => {
            const params = new URLSearchParams(window.location.search);
            const r = params.get('room');
            if (r) document.getElementById('roomId').value = r;
        };

        socket.on('user_joined', async (data) => {
            msg('chatMsg', `${data.username} присоединился`, 'success');
            document.getElementById('userCount').textContent = data.users;
            if (data.userId !== socket.id) {
                await createPeer(data.userId, true);
            }
        });

        socket.on('user_left', (data) => {
            msg('chatMsg', `${data.username} вышел`, 'warning');
            document.getElementById('userCount').textContent = data.users;
            if (peers[data.userId]) {
                peers[data.userId].close();
                delete peers[data.userId];
                const v = document.getElementById('v-' + data.userId);
                if (v) v.parentElement.remove();
            }
        });

        socket.on('offer', async (data) => {
            await createPeer(data.from, false);
            const offer = decrypt(data.offer, key);
            await peers[data.from].setRemoteDescription(JSON.parse(offer));
            const answer = await peers[data.from].createAnswer();
            await peers[data.from].setLocalDescription(answer);
            socket.emit('answer', { 
                to: data.from, 
                answer: encrypt(JSON.stringify(answer), key), 
                room 
            });
        });

        socket.on('answer', async (data) => {
            const answer = decrypt(data.answer, key);
            await peers[data.from].setRemoteDescription(JSON.parse(answer));
        });

        socket.on('ice_candidate', async (data) => {
            const cand = decrypt(data.candidate, key);
            if (peers[data.from]) {
                await peers[data.from].addIceCandidate(JSON.parse(cand));
            }
        });

        async function createPeer(id, isOffer) {
            const pc = new RTCPeerConnection(cfg);
            peers[id] = pc;

            stream.getTracks().forEach(t => pc.addTrack(t, stream));

            pc.ontrack = (e) => {
                let v = document.getElementById('v-' + id);
                if (!v) {
                    const box = document.createElement('div');
                    box.className = 'video-box';
                    box.innerHTML = `
                        <video id="v-${id}" autoplay playsinline></video>
                        <div class="video-label">Участник</div>
                    `;
                    document.getElementById('remote').appendChild(box);
                    v = document.getElementById('v-' + id);
                }
                v.srcObject = e.streams[0];
            };

            pc.onicecandidate = (e) => {
                if (e.candidate) {
                    socket.emit('ice_candidate', {
                        to: id,
                        candidate: encrypt(JSON.stringify(e.candidate), key),
                        room
                    });
                }
            };

            if (isOffer) {
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                socket.emit('offer', {
                    to: id,
                    offer: encrypt(JSON.stringify(offer), key),
                    room
                });
            }
        }

        function toggleVideo() {
            videoOn = !videoOn;
            stream.getVideoTracks()[0].enabled = videoOn;
            document.getElementById('videoBtn').textContent = videoOn ? '📹 Камера ВКЛ' : '📹 Камера ВЫКЛ';
        }

        function toggleAudio() {
            audioOn = !audioOn;
            stream.getAudioTracks()[0].enabled = audioOn;
            document.getElementById('audioBtn').textContent = audioOn ? '🎤 Микрофон ВКЛ' : '🎤 Микрофон ВЫКЛ';
        }

        function leave() {
            stream.getTracks().forEach(t => t.stop());
            Object.values(peers).forEach(p => p.close());
            socket.emit('leave', { room });
            location.reload();
        }

        function copy() {
            const inp = document.getElementById('shareUrl');
            inp.select();
            document.execCommand('copy');
            msg('chatMsg', 'Ссылка скопирована!', 'success');
        }

        function msg(id, text, type) {
            const el = document.getElementById(id);
            el.innerHTML = `<div class="status ${type}">${text}</div>`;
            setTimeout(() => el.innerHTML = '', 4000);
        }
    </script>
</body>
</html>
```

### 3. `requirements.txt`
```txt
flask==3.0.0
flask-socketio==5.3.5
python-socketio==5.10.0
eventlet==0.33.3
```

---

## 🚀 СПОСОБ 1: Быстрый запуск через ngrok (для теста)

### Шаги:

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Запустите сервер:**
```bash
python app.py
```

3. **Скачайте ngrok:** https://ngrok.com/download

4. **Запустите ngrok в новом терминале:**
```bash
ngrok http 5000
```

5. **Получите публичную ссылку:**
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

6. **Отправьте ссылку друзьям!** Они смогут зайти по этой ссылке из любой точки мира.

⚠️ **Минус:** При каждом перезапуске ngrok ссылка меняется (в бесплатной версии).

---

## 🌐 СПОСОБ 2: Бесплатный хостинг (постоянная ссылка)

### Render.com (рекомендую):

1. Зарегистрируйтесь на https://render.com
2. Создайте новый **Web Service**
3. Подключите GitHub репозиторий с вашим кодом
4. Render автоматически развернет приложение
5. Получите постоянную ссылку типа `https://ваш-чат.onrender.com`

**Или используйте:**
- **Railway.app** - https://railway.app
- **Fly.io** - https://fly.io
- **Heroku** - https://heroku.com (с платным планом)

---

## 📱 Как использовать:

1. Откройте ссылку (ngrok или хостинг)
2. Введите имя
3. Создайте комнату (или введите ID существующей)
4. Скопируйте ссылку кнопкой "📋 Копировать"
5. Отправьте друзьям: **ссылку + ключ шифрования**
6. Все заходят и видят друг друга!

---

## 🔒 Безопасность:

- ✅ Базовое XOR шифрование сигналов
- ✅ Уникальные ключи для каждой комнаты
- ✅ Видео/аудио передается напрямую (P2P через WebRTC)
- ⚠️ Для production используйте HTTPS и TURN серверы

Какой способ вам удобнее? Помочь с настройкой?