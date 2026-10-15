from fastapi import FastAPI

app = FastAPI(title="CartCare AI")


@app.get("/")
def root():
    return {"message": "CartCare AI backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}