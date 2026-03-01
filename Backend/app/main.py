from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, events, programs, departments, auth, attendance 
from app.services.face_recognition import FaceRecognitionService


app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(events.router)
app.include_router(programs.router)
app.include_router(departments.router)
app.include_router(auth.router)
app.include_router(attendance.router)

# Load face encodings at startup
face_service = FaceRecognitionService()
try:
    face_service.load_encodings("face_encodings.pkl")
except Exception:
    pass  # File may not exist yet, that's OK

# Auto-seed database on startup (creates tables, roles, admin user)
@app.on_event("startup")
def seed_database():
    try:
        from app.seeder import run_seeder
        run_seeder()
    except Exception as e:
        print(f"⚠️ Seeder warning: {e}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Student Attendance System API",
        "endpoints": {
            "users": "/users",
            "events": "/events",
            "programs": "/programs",
            "departments": "/departments"
        }
    }

@app.on_event("shutdown")
def save_face_encodings():
    face_service.save_encodings("face_encodings.pkl")