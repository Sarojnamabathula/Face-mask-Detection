import pytest
import numpy as np
from backend.vision import CentroidTracker, FaceMaskDetector

def test_centroid_tracker_registration():
    tracker = CentroidTracker(max_disappeared=5)
    # Give a single bounding box [startX, startY, endX, endY]
    rects = [(10, 10, 50, 50)]
    objects = tracker.update(rects)
    
    assert len(objects) == 1
    assert 0 in objects
    # Centroid should be (30, 30)
    assert objects[0] == (30, 30)

def test_centroid_tracker_disappearance():
    tracker = CentroidTracker(max_disappeared=2)
    tracker.update([(10, 10, 50, 50)])
    assert len(tracker.objects) == 1

    # Empty frame 1
    tracker.update([])
    assert len(tracker.objects) == 1
    assert tracker.disappeared[0] == 1

    # Empty frame 2
    tracker.update([])
    assert len(tracker.objects) == 1
    assert tracker.disappeared[0] == 2

    # Empty frame 3 -> exceeds max_disappeared (2) -> deregistered
    tracker.update([])
    assert len(tracker.objects) == 0

def test_detector_synthetic_frame():
    detector = FaceMaskDetector()
    # 480x640 blank frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = detector.process_frame(frame)
    
    assert "faces" in results
    assert "count" in results
    assert isinstance(results["faces"], list)
    assert results["count"] == len(results["faces"])

