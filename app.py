from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import random
import time
from datetime import datetime
import threading 


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///planes.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/planes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PlanesFrameDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icao = db.Column(db.String(4), nullable=False)
    speed = db.Column(db.Float, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    alt = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class PlaneFrameGenerator:
    def __init__(self, icao_list):
        self.icao_list = icao_list

    def generate_frame(self, icao):
        speed = random.uniform(800, 1000)
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        alt = random.randint(0, 50000)
        timestamp = datetime.now()

        print(f"Generated frame: {icao}, {speed}, {lat}, {lon}, {alt}, {timestamp}")
        return PlanesFrameDB(icao=icao, speed=speed, lat=lat, lon=lon, alt=alt, timestamp=timestamp)
    
    def generate_frames(self):
        while True:
            for icao in self.icao_list:
                frame = self.generate_frame(icao)
                save_frame_to_db(frame)
            time.sleep(1)

generator = PlaneFrameGenerator([''.join(random.choices('QWERTYUIOPASDFGHJKLZXCVBNM', k=4)) for _ in range(10)])

def start_generator():
    generator.generate_frames()


def save_frame_to_db(frame):
    with app.app_context():
        new_frame = PlanesFrameDB(
            icao=frame.icao,
            speed=frame.speed,
            lat=frame.lat,
            lon=frame.lon,
            alt=frame.alt,
            timestamp=frame.timestamp
        )
        db.session.add(new_frame)
        db.session.commit()

@app.route('/planes', methods=['GET'])
def get_planes():
    icao_list = generator.icao_list

    subquery = db.session.query(
        PlanesFrameDB.icao,
        db.func.max(PlanesFrameDB.timestamp).label('timestamp')
    ).filter(PlanesFrameDB.icao.in_(icao_list)).group_by(PlanesFrameDB.icao).subquery()

    latest_frames = db.session.query(PlanesFrameDB).join(
        subquery,
        (PlanesFrameDB.icao == subquery.c.icao) & (PlanesFrameDB.timestamp == subquery.c.timestamp)
    ).all()

    planes = []
    for frame in latest_frames:
        plane = {
            'icao' : frame.icao,
            'speed' : frame.speed,
            'lat' : frame.lat,
            'lon' : frame.lon,
            'alt' : frame.alt,
            'timestamp' : frame.timestamp
        }
        planes.append(plane)
    return jsonify({"planes": planes})

@app.route('/planeHistory', methods=['GET'])
def get_plane_history():
    icao = request.args.get('icao')
    frames = db.session.query(PlanesFrameDB).filter_by(icao=icao).order_by(PlanesFrameDB.timestamp.desc()).limit(50).all()

    history =[]
    for frame in frames:
        frame_data = {
            'id': frame.id,
            'icao': frame.icao,
            'speed': frame.speed,
            'lat': frame.lat,
            'lon': frame.lon,
            'alt': frame.alt,
            'timestamp': frame.timestamp
        }
        history.append(frame_data)
    return jsonify({"history": history})

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    threading.Thread(target=start_generator, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)