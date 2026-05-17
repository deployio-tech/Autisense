from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from analysis.emotion_variation_detector import EmotionVariationDetector


class EmotionRequest(BaseModel):
    video_path: str


app = FastAPI(
    title="Emotion Variation ML Service",
    description="Separate ML service for emotion variability",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in (
            os.environ.get("CORS_ORIGINS")
            or "https://autisense.deployio.tech,https://autisense-emotion.deployio.tech,http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "service": "Emotion Variation ML Service",
        "status": "running",
        "endpoints": ["/analyze-emotion"],
    }


@app.post("/analyze-emotion")
def analyze_emotion(request: EmotionRequest):
    video_path = request.video_path
    if not video_path:
        raise HTTPException(status_code=400, detail="video_path is required")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "analysis", "emotion_model_v2.pth"
    )

    try:
        logger.info(f"[EMOTION] Initializing detector with model: {model_path}")
        detector = EmotionVariationDetector(model_path)

        logger.info(f"[EMOTION] Analysis starting for: {video_path}")
        result = detector.analyze(video_path)

        logger.info(f"[EMOTION] Analysis complete - result: {result}")
        return {"emotion_variation": result["label"], "entropy": result["entropy"]}
    except Exception as exc:
        logger.error(f"[EMOTION] Error during analysis: {str(exc)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
