from sqlalchemy import Column, Integer, String, Float, DateTime
import datetime
from backend.database import Base

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class DetectionLog(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_utc_now, index=True)
    prediction = Column(String, index=True) # "Mask", "No Mask", "Incorrect Mask"
    confidence = Column(Float)
    image_path = Column(String, nullable=True)
    camera_id = Column(String, default="default_cam", index=True)
    tracking_id = Column(Integer, nullable=True, index=True)
