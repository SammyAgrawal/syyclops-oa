import json
import random
from datetime import datetime
# Base Device class
class Device:
    def __init__(self, device_id, zone_id, measurement_fields):
        self._device_id = device_id
        self._zone_id = zone_id
        self._measurement_info = measurement_fields
        self.building_id = "hyatt-place"
    
    def generate_message(self):
        raise NotImplementedError("Subclasses must implement this method")

# Temperature sensor implementation
class TemperatureSensor(Device):
    def __init__(self, id, zone_id=0):
        measurement_metadata = {
            "field": "temperature",
            "min-value": 65,
            "max-value": 85,
            "unit": "F",
            "type": int
        }
        super().__init__(f"temp-{id}", zone_id, measurement_metadata)
        
    def generate_message(self):
        value = random.randint(self._measurement_info["min-value"], self._measurement_info["max-value"])
        return json.dumps({
            "device_id": self._device_id,
            "zone_id": self._zone_id,
            "reading": value,
            "timestamp": datetime.now().isoformat(),
            "field": self._measurement_info["field"],
            "unit": self._measurement_info["unit"]
        })

# Humidity sensor implementation
class HumiditySensor(Device):
    def __init__(self, id, zone_id=0):
        measurement_metadata = {
            "field": "humidity",
            "min-value": 30,
            "max-value": 70,
            "unit": "%",
            "type": int
        }
        super().__init__(f"hum-{id}", zone_id, measurement_metadata)
        
    def generate_message(self):
        value = random.randint(self._measurement_info["min-value"], self._measurement_info["max-value"])
        return json.dumps({
            "device_id": self._device_id,
            "zone_id": self._zone_id,
            "reading": value,
            "timestamp": datetime.now().isoformat(),
            "field": self._measurement_info["field"],
            "unit": self._measurement_info["unit"]
        })

# CO2 sensor implementation
class CO2Sensor(Device):
    def __init__(self, id, zone_id=0):
        measurement_metadata = {
            "field": "co2",
            "min-value": 350,
            "max-value": 1500,
            "unit": "ppm",
            "type": int
        }
        super().__init__(f"co2-{id}", zone_id, measurement_metadata)
        
    def generate_message(self):
        value = random.randint(self._measurement_info["min-value"], self._measurement_info["max-value"])
        return json.dumps({
            "device_id": self._device_id,
            "zone_id": self._zone_id,
            "reading": value,
            "timestamp": datetime.now().isoformat(),
            "field": self._measurement_info["field"],
            "unit": self._measurement_info["unit"]
        })
