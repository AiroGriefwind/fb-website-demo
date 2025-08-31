import firebase_admin
from firebase_admin import credentials, db

def init_firebase():
    cred = credentials.Certificate("serviceAccountKey.json")          # ← your downloaded key
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://bp-cms-default-rtdb.asia-southeast1.firebasedatabase.app"    
    })

def save_json_to_firebase(path, data):
    db.reference(path).set(data)

def load_json_from_firebase(path):
    return db.reference(path).get()
