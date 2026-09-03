from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.agent import router as agent_router
from backend.api.dashborad import router as dashboard_router
from backend.api.roadmap import router as roadmap_router
from backend.api.submission import router as submission_router
from backend.api.progress import router as progress_router
from backend.api.user import router as user_router
app = FastAPI(
    title="AI DSA Tutor API",
    version= "1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(dashboard_router)
app.include_router(roadmap_router)
app.include_router(submission_router)
app.include_router(progress_router)
app.include_router(user_router)
@app.get("/health")
def health():
    return {
        "status":"ok"
    }