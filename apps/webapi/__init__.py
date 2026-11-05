from typing import NoReturn

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from webapi.api.editor_api import editor_router
from webapi.api.experiments_api import experiments_router
from webapi.api.game_api import game_router
from webapi.api.scenes_api import scenes_router

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
app.include_router(experiments_router)
