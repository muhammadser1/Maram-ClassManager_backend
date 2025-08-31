from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user,teacher,group_lessons,admin,student_payments,booking

# Initialize FastAPI app
app = FastAPI(
    title="Teacher Management System",
    description="An application to manage teacher and admin workflows for your institute.",
    version="1.0.0",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
app.include_router(group_lessons.router, prefix="/group_lessons", tags=["group_lessons"])
app.include_router(student_payments.router, prefix="/student_payments", tags=["student_payments"])
app.include_router(booking.router, prefix="/booking", tags=["booking"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Teacher Management System!"}


@app.on_event("startup")
def startup_event():
    """Run when FastAPI starts"""
    booking.start_scheduler()