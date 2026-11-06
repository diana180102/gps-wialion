from fastapi import FastAPI, APIRouter

app = FastAPI( title="GPS Wialon API", version="0.1.0" )

api = APIRouter(prefix="/api/v1")

@api.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(api)



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
