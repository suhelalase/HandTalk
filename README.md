# HandTalk - Real-Time Sign Language Recognition

🤖 **AI-powered real-time hand gesture recognition** converting ASL signs to text with audio output.

> ASL Real-time WebSocket inference.

## ✨ Features

- **Real-time Gesture Recognition**: WebSocket-based inference for low-latency processing (~30ms/frame)
- **ASL Support**: Pre-trained, ready to use
- **Text-to-Speech**: Automatic audio generation via Murf AI
- **Text Correction**: AI-powered grammar correction using Google Gemini
- **User-Friendly Interface**: Modern web UI with live hand skeleton overlay
- **Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/HandTalk.git
cd HandTalk

# Run with Docker Compose
docker-compose -f config/docker-compose.yml up
```

Open **http://localhost:3000** in your browser.

### Local Development

```bash
# Backend
cd apps/api
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001

# Frontend (new terminal)
cd apps/web
npm install
npm run dev
```

Open **http://localhost:3000**.

## 📁 Project Structure

```
HandTalk/
├── 📂 apps/                    # Source code
│   ├── api/                    # FastAPI backend
│   │   ├── src/               # Refactored application
│   │   ├── tests/             # Test suite
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── web/                    # Next.js frontend
│   │   ├── src/               # React application
│   │   └── Dockerfile
│
├── 📂 config/                  # Configuration files
│   ├── docker-compose.yml      # Local dev (web + api)
│   └── docker-compose.prod.yml # Production-ish example
│
├── 📂 .github/
│   └── workflows/             # CI/CD pipelines
│       ├── ci.yml            # Tests & validation
│       └── build-and-push.yml # DockerHub deployment
│
├── Makefile                    # Common commands
├── LICENSE
└── README.md                   # This file
```

## 🛠️ Quick Commands

```bash
make dev              # Start development environment
make test             # Run all tests
make lint             # Run linting
make build            # Build Docker images
make deploy           # Deploy to production
make clean            # Clean up Docker resources
```


## ⚙️ Configuration


- **Murf API key** and **Gemini API key** are entered in the UI (Settings) and stored locally in your browser.
- Nothing secret needs to be committed to the repo.


## 📊 How It Works

1. **Capture** → Camera captures hand gestures
2. **Detect** → MediaPipe detects 21 hand landmarks
3. **Predict** → CNN model predicts gesture group
4. **Disambiguate** → Landmark rules resolve to letters A-Z
5. **Accumulate** → Stable characters form words
6. **Speak** → Text auto-converted to speech

## ⚡ Performance

- **Latency**: ~30ms per frame
- **Accuracy**: ~95% gesture recognition
- **FPS**: 30+ fps recommended
- **Memory**: ~500MB API, ~300MB Web

## 🔐 Security

- API keys are user-provided in the UI and stored locally.
- For production, serve the web app over HTTPS and use `wss://` for the WebSocket.


## 🎯 Roadmap

- [ ] Multi-hand recognition
- [ ] Custom gesture training
- [ ] Video recording/playback
- [ ] Offline mode
- [ ] Mobile app (React Native)
- [ ] Additional sign languages
- [ ] Real-time confidence visualization

## 👏 Acknowledgments

- **MediaPipe** - Hand detection
- **TensorFlow/Keras** - ML framework
- **FastAPI/Next.js** - Web frameworks
- **Murf AI** - Text-to-speech API
- **Google Gemini** - Text correction API

