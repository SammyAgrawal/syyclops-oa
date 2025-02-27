from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, MetaData, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import time

# Get database connection parameters from environment variables
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_NAME = os.environ.get("DB_NAME", "building_data")
DB_USER = os.environ.get("DB_USER", "building_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "building_password")

# Create SQLAlchemy base
Base = declarative_base()


"""

System Design:
Imagine each building in the client's portfolio; the building is comprised of a set of zones (rooms, thermal divisions, floors, etc.)
Each zone is comprised of a set of devices (sensors, actuators, etc.)
Each device has a set of measurements (temperature, humidity, etc.)


"""


# Define the Zone model
class Zone(Base):
    __tablename__ = 'zones'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    square_footage = Column(Integer)  # Added square footage property
    
    # Relationships
    devices = relationship("Device", back_populates="zone")
    
    def __repr__(self):
        return f"<Zone(id={self.id}, name='{self.name}', square_footage={self.square_footage})>"

# Define the Device model
class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(String(50), primary_key=True)  # Using device_id as primary key
    zone_id = Column(Integer, ForeignKey('zones.id'))
    device_type = Column(String(50), nullable=False)
    
    # Relationships
    zone = relationship("Zone", back_populates="devices")
    measurements = relationship("Measurement", back_populates="device")
    
    def __repr__(self):
        return f"<Device(id='{self.id}', type='{self.device_type}', zone_id={self.zone_id})>"

# Define the Measurement model
class Measurement(Base):
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey('devices.id'))
    timestamp = Column(DateTime, nullable=False)
    field = Column(String(50), nullable=False)  # e.g., 'temperature', 'humidity'
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="measurements")
    
    def __repr__(self):
        return f"<Measurement(id={self.id}, device_id='{self.device_id}', field='{self.field}', value={self.value})>"

# Function to initialize the database
def init_db():
    # Create connection string
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    
    # Attempt to connect with retry logic
    max_retries = 5
    retry_delay = 5  # seconds
    
    for retry in range(max_retries):
        try:
            print(f"Connecting to database (attempt {retry+1}/{max_retries})...")
            engine = create_engine(db_url)
            
            # Create tables
            Base.metadata.create_all(engine)
            
            # Create session factory
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Initialize zones if they don't exist
            zone_count = session.query(Zone).count()
            if zone_count == 0:
                print("Initializing zones...")
                zones = [
                    Zone(id=1, name="Office Area", description="Main office workspace", square_footage=2500),
                    Zone(id=2, name="Conference Rooms", description="Meeting and conference areas", square_footage=1200),
                    Zone(id=3, name="Common Areas", description="Hallways, lobby, and break rooms", square_footage=1800)
                ]
                session.add_all(zones)
                session.commit()
                print(f"Added {len(zones)} zones to the database")
            
            session.close()
            print("Database initialized successfully")
            
            return engine, Session
        
        except Exception as e:
            print(f"Database connection failed: {e}")
            if retry < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries exceeded. Failed to connect to database.")
                raise
    
    # This shouldn't be reached due to the raise above, but just in case
    raise Exception("Failed to initialize database after multiple attempts")