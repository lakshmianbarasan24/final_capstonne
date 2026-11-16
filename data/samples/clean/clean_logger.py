import logging

logger = logging.getLogger(__name__)

def log_event(event_name: str, level: int = logging.INFO):
    if not event_name:
        return
    logger.log(level, f'Event: {event_name}')
