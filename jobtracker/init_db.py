from jobtracker.db import init_db
import logging


logger = logging.getLogger(__name__)


if __name__ == "__main__":
    init_db()
    logger.info("JobTracker database initialized")
