from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Carpetas para guardar archivos
os.makedirs('data/photos', exist_ok=True)
os.makedirs('data/audio',  exist_ok=True)

# Ubicaciones en memoria
locations = {}

# ── Recibe ubicación ──────────────────────────────────────────────
@app.route('/location', methods=['POST'])
def receive_location():
    data = request.get_json()
    if not all(k in data for k in ['driver_id', 'lat', 'lng']):
        return jsonify({'error': 'Faltan campos'}), 400

    driver_id = data['driver_id']
    is_emergency = data.get('emergency', False)

    locations[driver_id] = {
        'driver_id': driver_id,
        'lat':       data['lat'],
        'lng':       data['lng'],
        'accuracy':  data.get('accuracy'),
        'status':    'alert' if is_emergency else 'ok',
        'timestamp': datetime.utcnow().isoformat()
    }

    tag = '🚨 EMERGENCIA' if is_emergency else '📍'
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {tag} {driver_id} → {data['lat']:.5f}, {data['lng']:.5f}")
    return jsonify({'ok': True}), 200


# ── Entrega ubicaciones al dashboard ─────────────────────────────
@app.route('/locations', methods=['GET'])
def get_locations():
    return jsonify(list(locations.values())), 200


# ── Recibe foto ───────────────────────────────────────────────────
@app.route('/photo', methods=['POST'])
def receive_photo():
    driver_id = request.form.get('driver_id', 'unknown')
    timestamp = request.form.get('timestamp', datetime.utcnow().isoformat())
    photo     = request.files.get('photo')

    if not photo:
        return jsonify({'error': 'Sin foto'}), 400

    safe_ts   = timestamp.replace(':', '-').replace('.', '-')
    filename  = f"data/photos/{driver_id}_{safe_ts}.jpg"
    photo.save(filename)

    # Marcar como emergencia en el mapa
    if driver_id in locations:
        locations[driver_id]['status'] = 'alert'

    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] 📸 Foto recibida: {driver_id} → {filename}")
    return jsonify({'ok': True}), 200


# ── Recibe audio ──────────────────────────────────────────────────
@app.route('/audio', methods=['POST'])
def receive_audio():
    driver_id = request.form.get('driver_id', 'unknown')
    timestamp = request.form.get('timestamp', datetime.utcnow().isoformat())
    audio     = request.files.get('audio')

    if not audio:
        return jsonify({'error': 'Sin audio'}), 400

    safe_ts   = timestamp.replace(':', '-').replace('.', '-')
    filename  = f"data/audio/{driver_id}_{safe_ts}.webm"
    audio.save(filename)

    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] 🎙️ Audio recibido: {driver_id} → {filename}")
    return jsonify({'ok': True}), 200


# ── Health check ──────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'TransLog OK ✅', 'choferes': len(locations)}), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
