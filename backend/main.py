import cv2
import numpy as np
import io
import time
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import FastAPI, File, UploadFile, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import engine, Base, get_db
from backend.models import DetectionLog
from backend.vision import FaceMaskDetector

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Face Mask Detection API",
    description="Real-time Face Mask Detection, Tracking & Compliance Surveillance System"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vision Detector
detector = FaceMaskDetector()

# In-memory throttle cache: tracking_id -> (last_prediction, last_log_time)
_log_throttle = {}
THROTTLE_SECONDS = 4.0

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Face Mask Detection API",
        "model_loaded": detector.model is not None,
        "classes": detector.classes,
        "device": str(detector.device)
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the Face Mask Detection System API"}

@app.post("/predict")
async def predict_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Read image from upload
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file or format")

    # Process frame through vision engine (face detection, tracking & classification)
    results = detector.process_frame(frame)

    now = time.time()
    faces_to_log = []

    for face in results["faces"]:
        tid = face["tracking_id"]
        pred = face["prediction"]
        conf = face["confidence"]

        # Throttle writes to avoid locking SQLite with duplicate frames
        last_pred, last_time = _log_throttle.get(tid, (None, 0))
        should_log = (last_pred != pred) or (now - last_time >= THROTTLE_SECONDS)

        if should_log:
            _log_throttle[tid] = (pred, now)
            faces_to_log.append(
                DetectionLog(
                    prediction=pred,
                    confidence=conf,
                    tracking_id=tid,
                    camera_id="CAM-01"
                )
            )

    if faces_to_log:
        db.add_all(faces_to_log)
        db.commit()

    return results

@app.get("/api/history")
def get_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    prediction: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns paginated detection history logs with optional status filtering.
    """
    query = db.query(DetectionLog)
    if prediction and prediction.lower() != "all":
        query = query.filter(DetectionLog.prediction.ilike(f"%{prediction}%"))

    total = query.count()
    records = query.order_by(desc(DetectionLog.id)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "prediction": r.prediction,
                "confidence": r.confidence,
                "camera_id": r.camera_id,
                "tracking_id": r.tracking_id
            }
            for r in records
        ]
    }

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """
    Returns analytics metrics, compliance rate, and hourly distribution for the dashboard.
    """
    total = db.query(DetectionLog).count()

    # Counts by prediction class
    counts = (
        db.query(DetectionLog.prediction, func.count(DetectionLog.id))
        .group_by(DetectionLog.prediction)
        .all()
    )
    counts_dict = {pred: count for pred, count in counts}

    mask_count = counts_dict.get("Mask", 0)
    no_mask_count = counts_dict.get("No Mask", 0)
    incorrect_count = counts_dict.get("Incorrect Mask", 0)

    compliance_rate = round((mask_count / total * 100), 1) if total > 0 else 100.0

    # Hourly distribution for Recharts
    # Group by SQLite strftime hour
    hourly_query = (
        db.query(
            func.strftime("%H:00", DetectionLog.timestamp).label("hour"),
            func.count(DetectionLog.id).label("total")
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )

    hourly_data = [
        {"hour": h or "12:00", "detections": count}
        for h, count in hourly_query[-12:] # Last 12 recorded hours
    ]

    return {
        "total_detections": total,
        "compliance_rate": compliance_rate,
        "breakdown": {
            "mask": mask_count,
            "no_mask": no_mask_count,
            "incorrect_mask": incorrect_count
        },
        "pie_chart": [
            {"name": "Compliant (Mask)", "value": mask_count, "color": "#10b981"},
            {"name": "No Mask", "value": no_mask_count, "color": "#f43f5e"},
            {"name": "Incorrect Mask", "value": incorrect_count, "color": "#f59e0b"}
        ],
        "hourly_trend": hourly_data
    }

@app.delete("/api/history")
def clear_history(db: Session = Depends(get_db)):
    """
    Clears all detection records from the database.
    """
    db.query(DetectionLog).delete()
    db.commit()
    _log_throttle.clear()
    return {"message": "History logs successfully cleared"}
