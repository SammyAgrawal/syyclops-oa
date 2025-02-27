import clr
import sys
import os
import json
from datetime import datetime
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import revit, DB, script, forms

# Class to represent the building layout in Revit
class RevitBuildingLayout:
    def __init__(self, doc=None):
        """Initialize with the current Revit document or a provided one"""
        self.doc = doc if doc else revit.doc
        self.app = self.doc.Application
        
        # Dictionary to store zone mappings (BMS Zone ID -> Revit Room)
        self.zone_mappings = {}
        
        # Dictionary to store device mappings (BMS Device ID -> Revit FamilyInstance)
        self.device_mappings = {}
        
        # Load BMS zone definitions
        self.bms_zones = [
            {"id": 1, "name": "Office Area", "description": "Main office workspace", "square_footage": 2500},
            {"id": 2, "name": "Conference Rooms", "description": "Meeting and conference areas", "square_footage": 1200},
            {"id": 3, "name": "Common Areas", "description": "Hallways, lobby, and break rooms", "square_footage": 1800}
        ]
        
        # Define sensor types and their Revit family names
        self.sensor_types = {
            "temperature": "Temperature Sensor",
            "humidity": "Humidity Sensor",
            "co2": "CO2 Sensor"
        }
        
        # Define device locations (device_id -> [room_name, x_offset, y_offset, z_offset])
        self.device_locations = {
            # Zone 1 - Office Area
            "temp-1": ["Office 101", 2.5, 3.0, 2.4],  # Temperature sensor
            "hum-2": ["Office 101", 2.5, 3.2, 2.4],   # Humidity sensor
            "co2-3": ["Office 102", 1.8, 2.5, 2.4],   # CO2 sensor
            
            # Zone 2 - Conference Rooms
            "temp-4": ["Conference Room A", 3.0, 4.0, 2.4],  # Temperature sensor
            "hum-5": ["Conference Room A", 3.0, 4.2, 2.4],   # Humidity sensor
            "co2-6": ["Conference Room B", 2.5, 3.5, 2.4],   # CO2 sensor
            
            # Zone 3 - Common Areas
            "temp-7": ["Lobby", 5.0, 6.0, 2.4],       # Temperature sensor
            "hum-8": ["Hallway", 10.0, 2.0, 2.4]      # Humidity sensor
        }
    
    def map_zones_to_rooms(self):
        """Map BMS zones to Revit rooms based on name matching"""
        self.logger.info("Mapping BMS zones to Revit rooms...")
        
        # Get all rooms in the Revit model
        rooms = FilteredElementCollector(self.doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
        
        # Create a transaction for parameter updates
        with Transaction(self.doc, "Map BMS Zones to Rooms") as t:
            t.Start()
            
            # Map zones to rooms
            for zone in self.bms_zones:
                zone_id = zone["id"]
                zone_name = zone["name"]
                
                # Find rooms that belong to this zone
                zone_rooms = []
                
                for room in rooms:
                    room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
                    
                    # Map rooms to zones based on naming patterns
                    if zone_id == 1 and "Office" in room_name:
                        zone_rooms.append(room)
                        room.LookupParameter("BMS_Zone_ID").Set(str(zone_id))
                        room.LookupParameter("BMS_Zone_Name").Set(zone_name)
                    
                    elif zone_id == 2 and "Conference" in room_name:
                        zone_rooms.append(room)
                        room.LookupParameter("BMS_Zone_ID").Set(str(zone_id))
                        room.LookupParameter("BMS_Zone_Name").Set(zone_name)
                    
                    elif zone_id == 3 and any(area in room_name for area in ["Lobby", "Hallway", "Break"]):
                        zone_rooms.append(room)
                        room.LookupParameter("BMS_Zone_ID").Set(str(zone_id))
                        room.LookupParameter("BMS_Zone_Name").Set(zone_name)
                
                self.zone_mappings[zone_id] = zone_rooms
                self.logger.info(f"Zone {zone_id} ({zone_name}) mapped to {len(zone_rooms)} rooms")
            
            t.Commit()
        
        return self.zone_mappings
    
    def place_sensors(self):
        """Place sensor family instances in the Revit model at specified locations"""
        self.logger.info("Placing sensor devices in Revit model...")
        
        # Get all rooms in the Revit model
        rooms = FilteredElementCollector(self.doc).OfCategory(BuiltInCategory.OST_Rooms).ToElements()
        room_dict = {room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString(): room for room in rooms}
        
        # Create a transaction for adding sensor instances
        with Transaction(self.doc, "Place BMS Sensors") as t:
            t.Start()
            
            for device_id, location_data in self.device_locations.items():
                room_name, x_offset, y_offset, z_offset = location_data
                
                # Determine sensor type from device ID
                if "temp" in device_id:
                    sensor_type = "temperature"
                elif "hum" in device_id:
                    sensor_type = "humidity"
                elif "co2" in device_id:
                    sensor_type = "co2"
                else:
                    continue
                
                # Get the room
                if room_name in room_dict:
                    room = room_dict[room_name]
                    
                    # Get room location point
                    room_location = room.Location.Point
                    
                    # Create a point for the sensor
                    sensor_point = XYZ(
                        room_location.X + x_offset,
                        room_location.Y + y_offset,
                        room_location.Z + z_offset
                    )
                    
                    # Get the sensor family symbol
                    family_symbols = FilteredElementCollector(self.doc).OfClass(FamilySymbol)
                    sensor_symbol = None
                    
                    for symbol in family_symbols:
                        if symbol.Family.Name == self.sensor_types[sensor_type]:
                            sensor_symbol = symbol
                            break
                    
                    # If sensor family exists, place the instance
                    if sensor_symbol:
                        # Ensure symbol is activated
                        if not sensor_symbol.IsActive:
                            sensor_symbol.Activate()
                        
                        # Create the sensor instance
                        sensor_instance = self.doc.Create.NewFamilyInstance(
                            sensor_point, 
                            sensor_symbol, 
                            room.Level, 
                            StructuralType.NonStructural
                        )
                        
                        # Set parameters
                        sensor_instance.LookupParameter("BMS_Device_ID").Set(device_id)
                        sensor_instance.LookupParameter("BMS_Sensor_Type").Set(sensor_type)
                        
                        # Store in mappings
                        self.device_mappings[device_id] = sensor_instance
                        self.logger.info(f"Placed {sensor_type} sensor {device_id} in {room_name}")
                    else:
                        self.logger.warning(f"Sensor family {self.sensor_types[sensor_type]} not found in project")
                else:
                    self.logger.warning(f"Room {room_name} not found in Revit model")
            
            t.Commit()
        
        return self.device_mappings
    
    def import_bms_mapping(self, filepath):
        """Import a BMS-to-Revit mapping from a JSON file"""
        with open(filepath, 'r') as f:
            mapping_data = json.load(f)
        
        # Import zone mappings
        for zone_id, rooms_data in mapping_data["zones"].items():
            zone_id = int(zone_id)
            rooms = []
            
            for room_data in rooms_data:
                room_id = room_data["room_id"]
                room = self.doc.GetElement(ElementId(room_id))
                if room:
                    rooms.append(room)
            
            self.zone_mappings[zone_id] = rooms
        
        # Import device mappings
        for device_id, sensor_data in mapping_data["devices"].items():
            element_id = sensor_data["element_id"]
            sensor = self.doc.GetElement(ElementId(element_id))
            if sensor:
                self.device_mappings[device_id] = sensor
        
        self.logger.info(f"BMS mapping imported from {filepath}")
        return self.zone_mappings, self.device_mappings


# Example usage as a Revit command
def main():
    # Get the current Revit document
    doc = __revit__.ActiveUIDocument.Document
    
    # Create the building layout manager
    building = RevitBuildingLayout(doc)
    
    # Map zones to rooms
    zone_mappings = building.map_zones_to_rooms()
    
    # Place sensors in the model
    device_mappings = building.place_sensors()
    
    # Export the mapping for future use
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    export_path = os.path.join(desktop_path, "bms_revit_mapping.json")
    building.export_bms_mapping(export_path)
    
    # Show results
    forms.alert(
        "BMS Integration Complete\n"
        f"- {len(zone_mappings)} zones mapped to Revit rooms\n"
        f"- {len(device_mappings)} devices placed in the model\n"
        f"- Mapping exported to {export_path}",
        title="BMS-Revit Integration"
    )


# Execute the script
if __name__ == "__main__":
    main()


