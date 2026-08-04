# app/infrastructure/mqtt/consumer.py
import logging
from app.infrastructure.database.session import async_session_factory
from app.domain.services.telemetry_ingestion_service import TelemetryIngestionService

logger = logging.getLogger(__name__)

async def handle_mqtt_message(topic: str, payload: str) -> None:
    """
    Process incoming MQTT telemetry and route to ingestion service.
    """
    logger.info(f"Received MQTT message on topic '{topic}': {payload}")
    
    async with async_session_factory() as session:
        try:
            service = TelemetryIngestionService(session)
            await service.process_message(topic, payload)
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.exception(f"Failed to ingest MQTT message for topic {topic}: {e}")