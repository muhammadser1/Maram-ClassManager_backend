from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user
# Initialize FastAPI app
app = FastAPI(
    title="Teacher Management System",
    description="An application to manage teacher and admin workflows for your institute.",
    version="1.0.0",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router, prefix="/user", tags=["user"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Teacher Management System!"}