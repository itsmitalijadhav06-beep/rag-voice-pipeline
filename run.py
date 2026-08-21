"""
Application entrypoint runner for Voice-Enabled RAG Pipeline.
"""

import uvicorn
from app.core.config import settings


def main() -> None:
    """Launch the FastAPI server using Uvicorn."""
    uvicorn.run(
        "app.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
    )


if __name__ == "__main__":
    main()
