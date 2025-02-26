import json
import os
import time
from datetime import datetime
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from db_models import init_db, Device, Measurement

# Get MQTT broker details from environment
MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = "building/sensors/#"  # Subscribe to all sensor topics

class BuildingManagementSystem:
    def __init__(self):
        # Initialize database connection
        self.engine, self.SessionFactory = init_db()
        
        # Initialize MQTT client
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"Connected to MQTT broker at {MQTT_BROKER}")
            self.connected = True
            # Subscribe to the building sensors topic
            self.client.subscribe(MQTT_TOPIC)
            print(f"Subscribed to topic: {MQTT_TOPIC}")
        else:
            print(f"Failed to connect to MQTT broker with result code {rc}")
            self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            # Parse message payload
            payload = json.loads(msg.payload.decode())
            
            # Extract topic components
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 3:
                print(f"Invalid topic format: {msg.topic}")
                return
            
            print(f"Received message on topic {msg.topic}: {payload}")
            
            # Process and store the measurement
            self.process_measurement(payload)
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON payload: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def process_measurement(self, data):
        """Process and store measurement data in the database"""
        try:
            # Create a new database session
            session = self.SessionFactory()
            
            # Extract fields from the data
            device_id = data.get('device_id')
            zone_id = data.get('zone_id')
            reading = data.get('reading')
            timestamp_str = data.get('timestamp')
            field = data.get('field')
            unit = data.get('unit')
            
            # Convert timestamp string to datetime
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                timestamp = datetime.now()  # Fallback to current time
            
            # Check if device exists in the database
            device = session.query(Device).filter_by(id=device_id).first()
            if not device:
                # Create new device
                device_type = device_id.split('-')[0]  # Extract type from device_id (e.g., 'temp' from 'temp-1')
                device = Device(id=device_id, zone_id=zone_id, device_type=device_type)
                session.add(device)
                print(f"Added new device: {device_id}")
            
            # Create new measurement
            measurement = Measurement(
                device_id=device_id,
                timestamp=timestamp,
                field=field,
                value=float(reading),
                unit=unit
            )
            session.add(measurement)
            
            # Commit changes
            session.commit()
            print(f"Stored measurement: {field}={reading}{unit} for device {device_id}")
            
        except Exception as e:
            print(f"Error storing measurement: {e}")
            session.rollback()
        finally:
            session.close()
    
    def connect_mqtt(self):
        """Connect to the MQTT broker with retries"""
        retry_count = 0
        max_retries = 10
        
        while retry_count < max_retries and not self.connected:
            try:
                print(f"Attempting to connect to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} (attempt {retry_count+1}/{max_retries})...")
                #mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)
                self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
                return True
            except Exception as e:
                print(f"Connection failed: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(30, 2 ** retry_count)  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        if not self.connected:
            print("Failed to connect to MQTT broker after multiple attempts")
            return False
        
        return True
    
    def run(self):
        """Main method to run the Building Management System"""
        print("Starting Building Management System...")
        
        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.

        if self.connect_mqtt():
            try:
                # Start the MQTT loop                
                self.client.loop_forever()
            except KeyboardInterrupt:
                print("Shutting down...")
            finally:
                self.client.disconnect()
                print("Disconnected from MQTT broker")
        else:
            print("Could not start the Building Management System due to connection issues")

# Sample query methods that could be used for analysis
def get_zone_average_temperature(session, zone_id, start_time, end_time):
    """Get the average temperature for a zone during a specific time period"""
    from sqlalchemy import func
    return session.query(func.avg(Measurement.value)).\
        join(Device).\
        filter(
            Device.zone_id == zone_id,
            Measurement.field == 'temperature',
            Measurement.timestamp >= start_time,
            Measurement.timestamp <= end_time
        ).scalar()

def get_device_timeseries(session, device_id, field, start_time, end_time):
    """Get a timeseries of measurements for a specific device and field"""
    return session.query(Measurement.timestamp, Measurement.value).\
        filter(
            Measurement.device_id == device_id,
            Measurement.field == field,
            Measurement.timestamp >= start_time,
            Measurement.timestamp <= end_time
        ).order_by(Measurement.timestamp).all()

if __name__ == "__main__":
    # Allow time for the database and broker to start up
    print("Waiting for services to start...")
    time.sleep(10)
    
    # Create and run the Building Management System
    bms = BuildingManagementSystem()
    bms.run()