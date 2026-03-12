from pathlib import Path
import site
import sys

PROJECT_ROOT = Path(__file__).parent
PYDEPS = PROJECT_ROOT / "pydeps"
if PYDEPS.exists() and str(PYDEPS) not in sys.path:
    sys.path.insert(0, str(PYDEPS))

user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.append(user_site)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend_api:app", host="0.0.0.0", port=8000, reload=True)
