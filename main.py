from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Contract Intelligence API is running"}