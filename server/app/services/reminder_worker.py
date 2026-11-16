import asyncio
import logging

from ..config import settings
from ..database import SessionLocal
from .reminder import ReminderService

logger = logging.getLogger(__name__)


def process_due_reminders() -> int:
    """Обрабатывает наступившие напоминания в отдельной сессии."""
    db = SessionLocal()

    try:
        processed = ReminderService(db).process_due()
        db.commit()

        return processed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def reminder_worker_loop() -> None:
    while True:
        try:
            await asyncio.sleep(settings.reminders_worker_interval_seconds)
            processed = await asyncio.to_thread(process_due_reminders)

            if processed:
                logger.info("Processed %s reminders", processed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Reminder worker iteration failed")
