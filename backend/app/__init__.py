from fastapi import FastAPI

from app.modules.auth.auth_controller import router as auth_router

app = FastAPI(title="CineBook API", version="1.0.0")

app.include_router(auth_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
