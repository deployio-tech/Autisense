from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import traceback
import logging

from services.analysis.analyzer import VideoAnalyzer
from services.questionnaire_predictor import QuestionnairePredictor


class AnalyzeRequest(BaseModel):
    video_path: str


class QuestionnaireInput(BaseModel):
    responses: list[bool]
    age: int
    sex: str
    jaundice: str
    family_asd: str


app = FastAPI(
    title="Autism Behavior Detection ML Service",
    description="Pure ML backend for video-based autism behavior detection",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in (
            os.environ.get("CORS_ORIGINS")
            or "https://autisense.deployio.tech,https://autisense-ml.deployio.tech,http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

questionnaire_predictor = QuestionnairePredictor()


@app.get("/")
def read_root():
    return {
        "service": "Autism Behavior Detection ML Service",
        "status": "running",
        "endpoints": ["/analyze", "/predict/questionnaire"],
    }


@app.post("/predict/questionnaire")
def predict_questionnaire(data: QuestionnaireInput):
    try:
        questionnaire_data = {
            "responses": data.responses,
            "age": data.age,
            "sex": data.sex,
            "jaundice": data.jaundice,
            "family_asd": data.family_asd,
        }
        return questionnaire_predictor.predict(questionnaire_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze")
def analyze_video(request: AnalyzeRequest):
    video_path = request.video_path
    if not video_path:
        raise HTTPException(status_code=400, detail="video_path is required")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    analyzer = VideoAnalyzer()
    try:
        return analyzer.analyze(video_path)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
