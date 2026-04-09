from __future__ import annotations

import os
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException
import uvicorn

from sql_query_reviewer.models import ResetRequest, SQLReviewAction, SQLReviewState, StepResult
from server.environment import SQLReviewEnvironment


def create_app(environment: SQLReviewEnvironment | None = None) -> FastAPI:
    app = FastAPI(
        title="SQL Query Reviewer",
        description="OpenEnv-style SQL review environment served over FastAPI.",
        version="0.1.0",
    )
    env = environment or SQLReviewEnvironment()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/reset", response_model=StepResult)
    async def reset_environment(request: Annotated[ResetRequest | None, Body()] = None) -> StepResult:
        try:
            return env.reset(task_id=request.task_id if request else None)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/step", response_model=StepResult)
    async def step_environment(action: SQLReviewAction) -> StepResult:
        try:
            return env.step(action)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/state", response_model=SQLReviewState)
    async def get_state() -> SQLReviewState:
        try:
            return env.state()
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("server.app:app", host=host, port=port)


if __name__ == "__main__":
    main()
