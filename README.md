# 🎤 Telegram Voice Reply

Voice-controlled Telegram message replying system với FastAPI backend và WebSocket real-time communication.

## ✨ Features

- 🎤 **Voice Commands**: "Hey Viso, reply to Alice hello there"
- 📱 **Real-time Messages**: WebSocket integration với Telegram
- 🔢 **Index-based Replies**: "Reply to 3 ok got it"
- 🗣️ **TTS Feedback**: Phản hồi bằng giọng nói tiếng Việt
- 🚀 **Easy Deploy**: Hỗ trợ Railway, Render, Heroku

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <your-repo>
cd telegram-voice-reply
```

### 2. Backend Setup
```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt
cp .env.example .env
# Điền thông tin Telegram vào .env
python create_session.py
uvicorn src.main:app --reload
```

### 3. Frontend Setup
```bash
# Update SERVER URL trong client/app.js
# Serve static files hoặc deploy lên Vercel/Netlify
```

### 4. Deploy Production
```bash
# Railway
railway login && railway init && railway up

# Render
# Push to GitHub và connect trong Render dashboard

# Heroku
heroku create your-app && git push heroku main
```

## 📚 Documentation

- **Setup Guide**: `docs/setup.md`
- **Deployment**: `docs/deployment.md`
- **API Reference**: `docs/api.md`

## 🛠️ Development

```bash
# Run tests
cd server && python run_tests.py

# Code formatting
black src/ tests/
flake8 src/ tests/

# Type checking
mypy src/
```

## 🎯 Voice Commands

| Command | Example | Action |
|---------|---------|--------|
| `reply to <name>` | "Reply to Alice how are you" | Trả lời theo tên |
| `reply to <number>` | "Reply to 3 ok got it" | Trả lời theo index |
| `trả lời số <number>` | "Trả lời số 2 được rồi" | Tiếng Việt |
| `list messages` | "List messages" | Liệt kê tin gần đây |

## 📞 Support

- **Issues**: GitHub Issues
- **Docs**: [Viblo.asia](https://viblo.asia)
- **Community**: [TopDev.vn](https://topdev.vn)

## 📄 License

MIT License - see LICENSE file for details.


telegram-voice-reply/
├── server/                          # Backend FastAPI
│   ├── src/
│   │   ├── telegram/
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # Quản lý Telethon client
│   │   │   ├── handlers.py          # Xử lý tin nhắn Telegram
│   │   │   ├── schemas.py           # Models cho Telegram
│   │   │   └── config.py            # Cấu hình Telegram
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── websocket.py         # WebSocket endpoints
│   │   │   └── routes.py            # REST API routes
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Cấu hình tổng thể
│   │   │   └── logging.py           # Cấu hình logging
│   │   └── main.py                  # Entry point FastAPI
│   ├── requirements/
│   │   ├── base.txt                 # Dependencies cơ bản
│   │   ├── dev.txt                  # Tools phát triển
│   │   └── prod.txt                 # Requirements production
│   ├── sessions/                    # Thư mục session files
│   ├── .env                         # Biến môi trường
│   ├── .env.example                 # Template biến môi trường
│   ├── Procfile                     # Railway/Heroku config
│   ├── railway.toml                 # Railway config
│   ├── render.yaml                  # Render config
│   └── Dockerfile                   # Container config
├── client/                          # Frontend
│   ├── assets/
│   │   ├── porcupine_params.pv
│   │   └── Hey-Viso_en_wasm_v3_0_0.ppn
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── vercel.json
├── docs/                            # Tài liệu
│   ├── setup.md
│   ├── deployment.md
│   └── api.md
├── .gitignore
└── README.md