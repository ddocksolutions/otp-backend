from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, random, time
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
CORS(app)

otp_store = {}  # Temporary storage for OTPs

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(phone, otp):
    api_key = os.environ.get("FAST2SMS_API_KEY")
    message = f"Your OTP is {otp}"
    url = f"https://www.fast2sms.com/dev/bulkV2?authorization={api_key}&route=v3&message={message}&numbers={phone}"
    try:
        return requests.get(url).json()
    except:
        return None

@app.route('/request-otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    phone = data.get("phone")
    otp = generate_otp()
    otp_store[phone] = {"otp": otp, "expires": time.time() + 300}  # 5 min expiry
    if send_otp(phone, otp):
        return jsonify({"success": True})
    return jsonify({"success": False}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    phone = data.get("phone")
    otp = data.get("otp")
    record = otp_store.get(phone)
    if not record or record["otp"] != otp or time.time() > record["expires"]:
        return jsonify({"success": False, "message": "Invalid OTP"}), 400
    token = auth.create_custom_token(phone)
    del otp_store[phone]
    return jsonify({"success": True, "firebaseToken": token.decode('utf-8')})
  
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
