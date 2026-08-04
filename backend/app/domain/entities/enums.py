"""
Shared enums for the Device & Entity domain model.

Plain Python enums — no framework imports. These are the vocabulary every
other module (MQTT Manager, Automation Engine, API) speaks in.
"""
import enum


class DeviceType(str, enum.Enum):
    ENV_MONITOR = "env_monitor"
    ENV_CONTROL = "env_control"
    WATER_MONITOR = "water_monitor"
    WATER_CONTROL = "water_control"
    CAMERA = "camera"


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class EntityType(str, enum.Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"


class DeviceClass(str, enum.Enum):
    # Environment sensors
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    CO2 = "co2"
    O2 = "o2"
    PAR = "par"
    LIGHT_INTENSITY = "light_intensity"
    # Water sensors
    PH = "ph"
    EC = "ec"
    DISSOLVED_OXYGEN = "dissolved_oxygen"
    WATER_TEMPERATURE = "water_temperature"
    WATER_LEVEL = "water_level"
    # Environment actuators
    HUMIDIFIER = "humidifier"
    GROW_LIGHT = "grow_light"
    AIR_CONDITIONER = "air_conditioner"
    VENTILATION_FAN = "ventilation_fan"
    EXHAUST_FAN = "exhaust_fan"
    # Water actuators
    PERISTALTIC_PUMP = "peristaltic_pump"
    WATER_PUMP = "water_pump"
    DRAIN_VALVE = "drain_valve"
    FILL_VALVE = "fill_valve"
    MIXING_PUMP = "mixing_pump"
