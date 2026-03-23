from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Accessify API",
    description="Open-Source API für Barrierefreiheit in Dokumenten",
    version="0.1.0"
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}