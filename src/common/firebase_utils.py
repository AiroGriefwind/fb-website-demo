import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path

def init_firebase():
    if firebase_admin._apps:
        return
    key_path = Path("configs/secrets/serviceAccountKey.json")
    cred = credentials.Certificate(str(key_path))
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://bp-cms-default-rtdb.asia-southeast1.firebasedatabase.app"    
    })

def save_json_to_firebase(path, data):
    db.reference(path).set(data)

def load_json_from_firebase(path):
    return db.reference(path).get()
