import json
import random
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
USER = "hydrocore_backend"
PASSWORD = "changeme_in_prod"

# Compatible with paho-mqtt 2.x
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASSWORD)

print("Connecting to local Mosquitto broker...")
try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Failed to connect to broker: {e}")
    exit(1)

client.loop_start()

topic = "hydrocore/greenhouse-01/gh-a/env-monitor-01/telemetry"

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