from fastapi import FastAPI

app = FastAPI(title="Revise App", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True}