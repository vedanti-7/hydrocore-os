import json
import os
import random
import time
import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_BROKER_HOST", "localhost")
PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
USER = os.environ.get("MQTT_USERNAME", "hydrocore_backend")
PASSWORD = os.environ.get("MQTT_PASSWORD", "changeme_in_prod")

# Compatible with paho-mqtt 2.x
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASSWORD)

print(f"Connecting to Mosquitto broker at {BROKER}:{PORT}...") 
try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Failed to connect to broker: {e}")
    exit(1)

client.loop_start()

# Must match a provisioned devices.mqtt_client_id — ingestion resolves the
# device by this value alone and drops telemetry from unknown identities.
MQTT_CLIENT_ID = "env-monitor-dev-01"

topic = f"hydrocore/greenhouse-01/gh-a/{MQTT_CLIENT_ID}/telemetry"

print(f"Simulator started! Publishing telemetry every 5 seconds to topic:\n -> {topic}\n")

try:
    while True:
        payload = {
            "temperature": round(random.uniform(20.0, 28.0), 2),
            "humidity": round(random.uniform(50.0, 70.0), 2)
        }
        client.publish(topic, json.dumps(payload))
        print(f"Published: {payload}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nStopping simulator...")
    client.loop_stop()
    client.disconnect()