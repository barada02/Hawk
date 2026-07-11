"""Dev launcher — run the backend with `python main.py`.

For production, prefer running uvicorn/gunicorn directly against `app.main:app`.
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
