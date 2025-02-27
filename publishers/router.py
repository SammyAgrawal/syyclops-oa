import os
import paho.mqtt.client as mqtt
from devices import Device, TemperatureSensor, HumiditySensor, CO2Sensor
import logging
import logging.handlers
from datetime import datetime
import time

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mqtt_publisher')

# MQTT Publisher for devices
class DevicePublisher:
    def __init__(self, broker_host, topic_prefix="building/sensors"):
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.broker_host = broker_host
        self.topic_prefix = topic_prefix
        self.devices = []
        
    def add_device(self, device: Device):
        self.devices.append(device)
        
    def connect(self):
        logger.info(f"Connecting to MQTT broker at {self.broker_host}...")
        # Add connection retry logic
        retry_count = 0
        while retry_count < 3:
            try:
                self.client.connect(self.broker_host, 1883, 60)
                logger.info("Connected to MQTT broker!")
                return True
            except ConnectionRefusedError:
                retry_count += 1
                logger.info(f"Connection refused. Retrying in 3 seconds... ({retry_count}/3)")
                time.sleep(3)
        
        logger.error("Failed to connect to MQTT broker after 3 attempts")
        return False
        
    def publish_loop(self, interval=5):
        if not self.connect():
            return
        
        try:
            while True:
                for device in self.devices:
                    # Create device-specific topic
                    zone_topic = f"{self.topic_prefix}/zone{device._zone_id}/{device._measurement_info['field']}"
                    message = device.generate_message()
                    
                    # Publish message
                    result = self.client.publish(zone_topic, message)
                    status = result[0]
                    if status == 0:
                        logger.info(f"Published to {zone_topic}: {message}")
                    else:
                        logger.error(f"Failed to publish to {zone_topic}")
                    
                    # Small delay between device publishes
                    time.sleep(0.5)
                
                # Interval between rounds of publishing
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Publishing stopped")
        finally:
            self.client.disconnect()

# Main function to setup and run the publishers
def main():
    # Get broker host from environment or use default
    broker_host = os.environ.get("MQTT_BROKER", "mqtt-broker")
    
    # Create publisher
    publisher = DevicePublisher(broker_host, topic_prefix="hyatt-place/sensors")
    
    # Create multiple devices across different zones
    # Zone 1 (Office area)
    publisher.add_device(TemperatureSensor(1, zone_id=1))
    publisher.add_device(HumiditySensor(2, zone_id=1))
    publisher.add_device(CO2Sensor(3, zone_id=1))
    
    # Zone 2 (Conference rooms)
    publisher.add_device(TemperatureSensor(4, zone_id=2))
    publisher.add_device(HumiditySensor(5, zone_id=2))
    publisher.add_device(CO2Sensor(6, zone_id=2))
    
    # Zone 3 (Common areas)
    publisher.add_device(TemperatureSensor(7, zone_id=3))
    publisher.add_device(HumiditySensor(8, zone_id=3))
    
    # Start publishing with a 10-second interval
    logger.info("Starting to publish sensor data...")
    publisher.publish_loop(interval=10)

if __name__ == "__main__":
    # Allow time for the broker to start up
    print("Waiting for services to start...")
    time.sleep(10)
    main()