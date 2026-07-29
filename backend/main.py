from fastapi import FastAPI

app = FastAPI(title="Hydrocore OS Backend")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "hydrocore-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
