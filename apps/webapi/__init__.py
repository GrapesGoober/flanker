from typing import NoReturn

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from webapi.editor_api import router as editor_router
from webapi.game_api import router as game_router
from webapi.scenes_api import router as scenes_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
@app.exception_handler(ValidationError)
async def value_error_handler(_: Request, exc: Exception) -> NoReturn:
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


app.include_router(scenes_router)
app.include_router(game_router)
app.include_router(editor_router)
