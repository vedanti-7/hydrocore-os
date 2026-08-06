"""
MQTT topic contract.

The single definition of what a HydroCore telemetry topic looks like. Both
the subscriber and the ingestion service depend on this module so the
firmware-facing contract lives in exactly one place.

Telemetry topic format (exactly five segments):

    hydrocore/{site}/{greenhouse}/{mqtt_client_id}/telemetry

Example:

    hydrocore/test-site/greenhouse-01/esp32-01/telemetry

Segment 4 is the authoritative physical device identity: it must match a
provisioned devices.mqtt_client_id, which is UNIQUE. Segments 2 and 3 are
routing/readability hints only — ownership lives in the database, and a
mismatch never moves a device.

The subscription is a wildcard, so non-telemetry topics under hydrocore/#
(status, command, ... ) will also arrive. Those must parse to None and be
ignored rather than guessed at.
"""
import re
from dataclasses import dataclass

TELEMETRY_ROOT = "hydrocore"
TELEMETRY_SUFFIX = "telemetry"
TELEMETRY_TOPIC_FILTER = f"{TELEMETRY_ROOT}/#"

# The identity segment is matched against devices.mqtt_client_id
# (String(120)) and feeds entities.unique_id (String(160)) as
# "{mqtt_client_id}/{metric}". Bounding here keeps a long topic from
# turning into a database error deep inside ingestion.
MAX_SEGMENT_LENGTH = 120

# Deliberately strict: identifiers only. Excludes MQTT wildcards (+, #),
# whitespace and path separators that would make an ambiguous unique_id.
_SEGMENT_PATTERN = re.compile(rf"^[A-Za-z0-9][A-Za-z0-9._:-]{{0,{MAX_SEGMENT_LENGTH - 1}}}$")


@dataclass(frozen=True)
class TelemetryTopic:
    """
    A validated telemetry topic.

    site/greenhouse are hints for humans reading the broker; mqtt_client_id
    is the identity ingestion actually resolves against.
    """

    site: str
    greenhouse: str
    mqtt_client_id: str


def parse_telemetry_topic(topic: str) -> TelemetryTopic | None:
    """
    Return the parsed topic, or None if it is not a well-formed telemetry topic.

    None covers both "malformed" and "valid but not telemetry" — in either
    case the correct action is the same: ingest nothing.
    """
    if not topic:
        return None

    segments = topic.strip("/").split("/")
    if len(segments) != 5:
        return None

    root, site, greenhouse, mqtt_client_id, suffix = segments
    if root != TELEMETRY_ROOT or suffix != TELEMETRY_SUFFIX:
        return None

    if not all(
        _SEGMENT_PATTERN.fullmatch(segment)
        for segment in (site, greenhouse, mqtt_client_id)
    ):
        return None

    return TelemetryTopic(site=site, greenhouse=greenhouse, mqtt_client_id=mqtt_client_id)
