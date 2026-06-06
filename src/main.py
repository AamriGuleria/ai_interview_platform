from typing import Annotated

from fastapi import Depends, FastAPI
import uvicorn 
from apis import api_router

app = FastAPI()



@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI"}

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)