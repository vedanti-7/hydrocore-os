import asyncio
import logging
import aiomqtt
from app.core.config import get_settings
from app.infrastructure.mqtt.consumer import handle_mqtt_message

logger = logging.getLogger(__name__)

async def start_mqtt_listener():
    settings = get_settings()

    broker = settings.mqtt_host
    port = settings.mqtt_port
    username = settings.mqtt_username
    password = settings.mqtt_password

    while True:
        try:
            logger.info(f"Connecting to MQTT broker at {broker}:{port}...")
            async with aiomqtt.Client(
                hostname=broker,
                port=port,
                username=username,
                password=password,
            ) as client:
                logger.info("Connected to MQTT broker. Subscribing to hydrocore/#...")
                await client.subscribe("hydrocore/#")
                
                async for message in client.messages:
                    raw_payload = message.payload
                    if isinstance(raw_payload, (bytes, bytearray)):
                        payload = raw_payload.decode("utf-8", errors="replace")
                    elif raw_payload is None:
                        payload = ""
                    else:
                        payload = str(raw_payload)

                    topic = str(message.topic)
                    await handle_mqtt_message(topic, payload)

        except aiomqtt.MqttError as e:
            logger.error(f"MQTT error occurred: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("MQTT listener shutting down...")
            break
        except Exception as e:
            logger.exception(f"Unexpected error in MQTT listener: {e}")
            await asyncio.sleep(5)