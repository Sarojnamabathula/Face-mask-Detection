import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import cv2
import numpy as np
import mediapipe as mp
import math
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from typing import List, Dict, Any, Tuple, Optional

# A centroid tracker for assigning persistent IDs to faces
class CentroidTracker:
    def __init__(self, max_disappeared: int = 40):
        self.next_object_id = 0
        self.objects: Dict[int, Tuple[int, int]] = {}
        self.disappeared: Dict[int, int] = {}
        self.max_disappeared = max_disappeared

    def register(self, centroid: Tuple[int, int]):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id: int):
        if object_id in self.objects:
            del self.objects[object_id]
        if object_id in self.disappeared:
            del self.disappeared[object_id]

    def update(self, rects: List[Tuple[int, int, int, int]]) -> Dict[int, Tuple[int, int]]:
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(tuple(input_centroids[i]))
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Distance matrix between tracked centroids and new centroids
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = tuple(input_centroids[col])
                self.disappeared[object_id] = 0

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    self.register(tuple(input_centroids[col]))

        return self.objects


class FaceMaskDetector:
    DEFAULT_CLASSES = ["Mask", "No Mask", "Incorrect Mask"]

    def __init__(self, model_path: Optional[str] = None):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.tracker = CentroidTracker(max_disappeared=40)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        # Candidate model weight paths
        candidates = [
            model_path,
            os.path.join(os.path.dirname(__file__), "..", "models", "best_mobilenetv2_fmd.pth"),
            os.path.join("models", "best_mobilenetv2_fmd.pth"),
        ]
        self.model = None
        self.classes = self.DEFAULT_CLASSES

        # PyTorch preprocessing transform for MobileNetV2
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        for path in candidates:
            if path and os.path.exists(path):
                self._load_pytorch_model(path)
                break

        if self.model is None:
            print("[FaceMaskDetector] Notice: No pre-trained PyTorch weights found in 'models/'. Running in fallback mode.")

    def _load_pytorch_model(self, path: str):
        try:
            print(f"[FaceMaskDetector] Loading MobileNetV2 weights from {path}...")
            checkpoint = torch.load(path, map_location=self.device)
            
            # Detect saved classes from checkpoint
            if isinstance(checkpoint, dict) and "classes" in checkpoint and checkpoint["classes"]:
                self.classes = checkpoint["classes"]

            num_classes = len(self.classes)
            
            # Build MobileNetV2 architecture matching training
            net = models.mobilenet_v2(weights=None)
            net.classifier[1] = nn.Sequential(
                nn.Dropout(p=0.4),
                nn.Linear(net.last_channel, num_classes)
            )

            # Support state_dict or raw model checkpoint
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                net.load_state_dict(checkpoint["state_dict"])
            elif isinstance(checkpoint, dict):
                net.load_state_dict(checkpoint)
            else:
                net = checkpoint

            net.to(self.device)
            net.eval()
            self.model = net
            print(f"[FaceMaskDetector] Model loaded successfully with classes: {self.classes}")
        except Exception as e:
            print(f"[FaceMaskDetector] Error loading model from {path}: {e}")
            self.model = None

    def predict_mask(self, face_img: np.ndarray) -> Tuple[str, float]:
        """
        Inference engine for mask classification using MobileNetV2 if available,
        otherwise uses a color/heuristic check on the lower face half.
        """
        if face_img is None or face_img.size == 0 or face_img.shape[0] < 10 or face_img.shape[1] < 10:
            return "No Mask", 0.50

        if self.model is not None:
            try:
                rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_img)
                tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    outputs = self.model(tensor)
                    probabilities = torch.softmax(outputs, dim=1)[0]
                    confidence, pred_idx = torch.max(probabilities, dim=0)

                pred_idx = pred_idx.item()
                if pred_idx < len(self.classes):
                    return self.classes[pred_idx], round(float(confidence.item()), 2)
            except Exception as e:
                print(f"[FaceMaskDetector] Inference error: {e}")

        # Deterministic heuristic fallback when weights file is not yet trained:
        # Analyzes color variance and texture of lower half (mouth/nose) vs upper half (forehead)
        h, w, _ = face_img.shape
        lower_half = face_img[int(h * 0.5):, :]
        hsv_lower = cv2.cvtColor(lower_half, cv2.COLOR_BGR2HSV)
        # Skin color heuristic in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv_lower, lower_skin, upper_skin)
        skin_ratio = np.sum(skin_mask > 0) / float(skin_mask.size)

        if skin_ratio < 0.28:
            return "Mask", 0.92
        elif skin_ratio > 0.65:
            return "No Mask", 0.90
        else:
            return "Incorrect Mask", 0.82

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Processes a single frame: detects faces, tracks them, and predicts mask status.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)

        rects = []
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                xmin = int(bboxC.xmin * w)
                ymin = int(bboxC.ymin * h)
                width = int(bboxC.width * w)
                height = int(bboxC.height * h)

                # Ensure bounding box is within frame boundaries
                xmin = max(0, xmin)
                ymin = max(0, ymin)
                xmax = min(w, xmin + width)
                ymax = min(h, ymin + height)

                if xmax > xmin and ymax > ymin:
                    rects.append((xmin, ymin, xmax, ymax))

        # Update tracker with current faces
        objects = self.tracker.update(rects)

        # Match tracked centroids to nearest bounding boxes
        tracked_faces = []
        for (object_id, centroid) in objects.items():
            cx, cy = centroid

            best_rect = None
            min_dist = float("inf")
            for rect in rects:
                xmin, ymin, xmax, ymax = rect
                rx = (xmin + xmax) // 2
                ry = (ymin + ymax) // 2
                dist = math.hypot(cx - rx, cy - ry)
                if dist < min_dist:
                    min_dist = dist
                    best_rect = rect

            if best_rect is not None and min_dist < max(w, h) * 0.25:
                xmin, ymin, xmax, ymax = best_rect
                face_crop = frame[ymin:ymax, xmin:xmax]
                label, confidence = self.predict_mask(face_crop)

                tracked_faces.append({
                    "tracking_id": int(object_id),
                    "bbox": [int(xmin), int(ymin), int(xmax - xmin), int(ymax - ymin)],
                    "prediction": label,
                    "confidence": float(confidence)
                })

        return {
            "faces": tracked_faces,
            "count": len(tracked_faces)
        }
