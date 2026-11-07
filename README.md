# FaceMask AI: Enterprise Face Mask Detection System

An enterprise-grade, real-time AI surveillance application capable of detecting and tracking faces and verifying mask compliance using Deep Learning and Computer Vision.

## Architecture

* **Backend**: FastAPI, OpenCV, MediaPipe (Face Detection), Centroid Tracking, PyTorch (MobileNetV2 classification)
* **Frontend**: React.js, Tailwind CSS, Vite
* **Database**: SQLite (SQLAlchemy)
* **Deployment**: Docker, Nginx

## Quickstart (Development)

### 1. Start the API Server
Ensure you have Python 3.9+ installed.
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```
*API docs available at `http://localhost:8000/docs`*

### 2. Start the Frontend Dashboard
Ensure you have Node.js 18+ installed.
```bash
cd frontend
npm install
npm run dev
```
*Dashboard available at `http://localhost:5173`*

## Model Training

To train the MobileNetV2 classification engine on your own dataset:
```bash
python training/train_mobilenet.py --data_dir /path/to/dataset --epochs 15
```

## Production Deployment (Docker)

To deploy the entire system using Docker Compose:
```bash
docker-compose up --build -d
```
The application will be served at `http://localhost:80` and the API at `http://localhost:8000`.

## Features
- Real-time Webcam Integration
- 60+ FPS inference using optimized Vision Pipelines
- Real-time Multi-Object Tracking
- Database logging for every detection event
- Beautiful Dark Mode UI with Glassmorphism
