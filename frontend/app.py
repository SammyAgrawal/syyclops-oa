from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker
import os
import time

app = Flask(__name__)

# Database connection
DB_USER = os.environ.get('DB_USER', 'building_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'building_password')
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'building_data')

# Create SQLAlchemy engine and session
def get_db_session():
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

@app.route('/')
def index():
    # Get all zones for the dropdown
    session = get_db_session()
    zones = session.execute(text("SELECT id, name FROM zones")).fetchall()
    session.close()
    return render_template('index.html', zones=zones)

@app.route('/zone_data', methods=['POST'])
def zone_data():
    zone_id = request.form.get('zone_id')
    if not zone_id:
        return jsonify({"error": "No zone selected"}), 400
    
    session = get_db_session()
    
    # Get zone name
    zone = session.execute(text("SELECT name FROM zones WHERE id = :zone_id"), 
                          {"zone_id": zone_id}).fetchone()
    
    # Get recent measurements for devices in the selected zone
    query = text("""
    SELECT m.id, d.id as device_id, d.device_type, m.value, m.timestamp
    FROM measurements m
    JOIN devices d ON m.device_id = d.id
    WHERE d.zone_id = :zone_id
    ORDER BY m.timestamp DESC
    LIMIT 10
    """)
    
    measurements = session.execute(query, {"zone_id": zone_id}).fetchall()
    session.close()
    
    return jsonify({
        "zone_name": zone[0] if zone else "Unknown Zone",
        "measurements": [
            {
                "id": m[0],
                "device_id": m[1],
                "device_type": m[2],
                "value": m[3],
                "timestamp": m[4].strftime("%Y-%m-%d %H:%M:%S") if m[4] else None
            } for m in measurements
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

