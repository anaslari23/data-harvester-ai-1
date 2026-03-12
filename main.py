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

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):
        return False

from config.settings import load_settings
from core.orchestrator import Orchestrator
from utils.logger import setup_logging


def main() -> None:
    project_root = Path(__file__).parent
    load_dotenv(project_root / ".env")

    logger = setup_logging(project_root / "output" / "logs")
    logger.info("DataHarvester starting up")

    settings = load_settings(project_root)
    orchestrator = Orchestrator(project_root=project_root, settings=settings, logger_instance=logger)

    orchestrator.run()


if __name__ == "__main__":
    main()
