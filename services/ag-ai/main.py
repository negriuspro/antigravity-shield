"""
ag-ai — AI-powered Ad Detection Microservice
Phase 1: Stub with simulated responses.
Phase 2: Integrate ONNX + YOLO for visual ad detection.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import random
import time
import os

app = FastAPI(
    title="AntiGravity AI Service",
    description="Visual ad detection — Phase 1 stub",
    version="0.1.0-stub",
)

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

# --- Schemas ---

class DomainClassification(BaseModel):
    domain: str
    is_ad: bool
    confidence: float
    category: str
    method: str

class ImageAnalysisResult(BaseModel):
    is_ad: bool
    confidence: float
    detections: list[dict]
    processing_ms: float
    model: str


# --- Routes ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ag-ai", "mode": "stub"}


@app.post("/classify/domain", response_model=DomainClassification)
async def classify_domain(domain: str):
    """
    Classify a domain as ad/tracker or legitimate.
    Phase 1: heuristic-based stub.
    Phase 2: ML model trained on domain features.
    """
    ad_keywords = ["ad", "ads", "advert", "banner", "track", "pixel", "analytics",
                   "doubleclick", "googlesyndication", "facebook", "amazon-adsystem",
                   "taboola", "outbrain", "scorecardresearch", "omtrdc"]

    lower = domain.lower()
    is_ad = any(kw in lower for kw in ad_keywords)
    confidence = round(random.uniform(0.75, 0.99) if is_ad else random.uniform(0.05, 0.30), 3)

    return DomainClassification(
        domain=domain,
        is_ad=is_ad,
        confidence=confidence,
        category="advertising" if is_ad else "content",
        method="heuristic-v1",
    )


@app.post("/analyze/image", response_model=ImageAnalysisResult)
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze a screenshot for visual ads (banners, popups).
    Phase 1: simulated response.
    Phase 2: YOLO + ONNX Runtime inference.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    start = time.perf_counter()
    # Simulate processing time
    time.sleep(0.05)
    elapsed = (time.perf_counter() - start) * 1000

    # Stub detection
    mock_detections = []
    if random.random() > 0.5:
        mock_detections = [
            {"label": "banner_ad", "confidence": round(random.uniform(0.7, 0.95), 3),
             "bbox": [10, 0, 990, 90]},
        ]

    return ImageAnalysisResult(
        is_ad=len(mock_detections) > 0,
        confidence=mock_detections[0]["confidence"] if mock_detections else 0.0,
        detections=mock_detections,
        processing_ms=round(elapsed, 2),
        model="stub-v1 (YOLO integration pending)",
    )


@app.get("/models")
async def list_models():
    """List available AI models — Phase 2 will serve real ONNX models."""
    return {
        "models": [],
        "note": "Phase 1 stub. ONNX/YOLO models will be loaded in Phase 2.",
        "roadmap": {
            "phase_2": "YOLOv8 domain classification",
            "phase_3": "Visual banner/popup detection via ONNX Runtime",
            "phase_4": "Real-time traffic stream analysis",
        }
    }
