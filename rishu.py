import json
import binascii
import time
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import requests
import urllib3
from flask import Flask, request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CREDIT CHOR KI TO MKC
import my_pb2
import output_pb2

app = Flask(__name__)

# -------------------- Constants --------------------
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV  = b'6oyZDr22E3ychjM%'
WISHLIST_URL = "https://client.ind.freefiremobile.com/ChangeWishListItem"

OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
MAJOR_LOGIN_URL = "https://loginbp.ggblueshark.com/MajorLogin"
INSPECT_URL = "https://100067.connect.garena.com/oauth/token/inspect"

CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
CLIENT_ID = "100067"

LOGIN_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
    "Connection": "Keep-Alive",
    "Content-Type": "application/octet-stream",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": "OB53",
}

# -------------------- Helper Functions --------------------
def varint_encode(n: int) -> bytes:
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)

def encrypt_data(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def build_wishlist_payload(item_id: int, add: bool) -> bytes:
    identifier_bytes = varint_encode(item_id)
    def encode_field(num: int, value: bytes) -> bytes:
        tag = (num << 3) | 2
        tag_bytes = varint_encode(tag)
        len_bytes = varint_encode(len(value))
        return tag_bytes + len_bytes + value

    plain = b''
    if add:
        plain += encode_field(1, identifier_bytes)
        plain += encode_field(3, b"Gacha")
    else:
        plain += encode_field(2, identifier_bytes)
        plain += encode_field(4, b"WishList")
    return encrypt_data(plain)

def get_open_id_from_access_token(access_token: str) -> str:
    
    try:
        resp = requests.get(INSPECT_URL, params={"token": access_token}, timeout=10, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("open_id")
    except:
        pass
    return None

def get_jwt_from_access_token(access_token: str, open_id: str = None) -> str:
    
    if not open_id:
        open_id = get_open_id_from_access_token(access_token)
        if not open_id:
            return None

    # Try platforms 1..9 (as in guest flow)
    for pt in range(1, 10):
        try:
            game = my_pb2.GameData()
            game.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            game.game_name = "free fire"
            game.game_version = 1
            game.version_code = "2.124.1"
            game.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game.device_type = "Handheld"
            game.network_provider = "Verizon Wireless"
            game.connection_type = "WIFI"
            game.screen_width = 1280
            game.screen_height = 960
            game.dpi = "240"
            game.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game.total_ram = 5951
            game.gpu_name = "Adreno (TM) 640"
            game.gpu_version = "OpenGL ES 3.0"
            game.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game.ip_address = "172.190.111.97"
            game.language = "en"
            game.open_id = open_id
            game.access_token = access_token
            game.platform_type = pt
            game.field_99 = str(pt)
            game.field_100 = str(pt)

            ser = game.SerializeToString()
            enc = encrypt_data(ser)
            resp = requests.post(MAJOR_LOGIN_URL, data=enc, headers=LOGIN_HEADERS, verify=False, timeout=10)
            if resp.status_code == 200:
                msg = output_pb2.Garena_420()
                msg.ParseFromString(resp.content)
                if msg.token:
                    return msg.token
        except:
            continue
        time.sleep(0.1)
    return None

def get_jwt_from_guest(uid: str, password: str) -> str:
    
    oauth_data = {
        'uid': uid,
        'password': password,
        'response_type': 'token',
        'client_type': '2',
        'client_secret': CLIENT_SECRET,
        'client_id': CLIENT_ID
    }
    oauth_headers = {'User-Agent': 'GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;pt;BR;)'}
    try:
        oauth_resp = requests.post(OAUTH_URL, data=oauth_data, headers=oauth_headers, timeout=10, verify=False)
        if oauth_resp.status_code != 200:
            return None
        oauth_json = oauth_resp.json()
        access_token = oauth_json.get('access_token')
        open_id = oauth_json.get('open_id')
        if not access_token or not open_id:
            return None
    except:
        return None

    # MajorLogin with platforms 1..9
    for pt in range(1, 10):
        try:
            game = my_pb2.GameData()
            game.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            game.game_name = "free fire"
            game.game_version = 1
            game.version_code = "2.124.1"
            game.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game.device_type = "Handheld"
            game.network_provider = "Verizon Wireless"
            game.connection_type = "WIFI"
            game.screen_width = 1280
            game.screen_height = 960
            game.dpi = "240"
            game.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game.total_ram = 5951
            game.gpu_name = "Adreno (TM) 640"
            game.gpu_version = "OpenGL ES 3.0"
            game.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game.ip_address = "172.190.111.97"
            game.language = "en"
            game.open_id = open_id
            game.access_token = access_token
            game.platform_type = pt
            game.field_99 = str(pt)
            game.field_100 = str(pt)

            ser = game.SerializeToString()
            enc = encrypt_data(ser)
            resp = requests.post(MAJOR_LOGIN_URL, data=enc, headers=LOGIN_HEADERS, verify=False, timeout=10)
            if resp.status_code == 200:
                msg = output_pb2.Garena_420()
                msg.ParseFromString(resp.content)
                if msg.token:
                    return msg.token
        except:
            continue
        time.sleep(0.1)
    return None

def add_to_wishlist(jwt: str, item_id: int):
    encrypted = build_wishlist_payload(item_id, add=True)
    headers = {
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Authorization": f"Bearer {jwt}",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2022.3.47f1",
        "Host": "clientbp.ggpolarbear.com",
        "Connection": "keep-alive"
    }
    try:
        resp = requests.post(WISHLIST_URL, headers=headers, data=encrypted, timeout=15, verify=False)
        return (resp.status_code == 200, resp.status_code, None)
    except Exception as e:
        return (False, 500, str(e))

# -------------------- Flask Route --------------------
@app.route('/add/<int:item_id>', methods=['GET', 'POST'])
def add_item(item_id):
    # Authentication parameters
    jwt = request.args.get('jwt')
    uid = request.args.get('uid')
    password = request.args.get('password')
    access_token = request.args.get('access_token')
    open_id = request.args.get('open_id')   # optional for access_token method

    # Validate item_id (already int from route)
    if item_id <= 0:
        return "ERROR: Invalid item_id (must be positive integer)", 400

    
    if jwt:
        
        pass
    elif uid and password:
        jwt = get_jwt_from_guest(uid, password)
        if not jwt:
            return "ERROR: Failed to generate JWT from guest credentials", 401
    elif access_token:
        jwt = get_jwt_from_access_token(access_token, open_id)
        if not jwt:
            return "ERROR: Failed to generate JWT from access token", 401
    else:
        return "ERROR: Either 'jwt', 'uid+password', or 'access_token' is required", 400

    success, status_code, error_msg = add_to_wishlist(jwt, item_id)
    if success:
        return f"ITEM ADDED SUCCESSFUL\nSTATUS {status_code} OK", 200
    else:
        return f"ERROR: Failed to add item (HTTP {status_code})\nDetails: {error_msg if error_msg else 'Server returned error'}", status_code
@app.route('/', methods=['GET', 'POST'])
def handle_request():
    action = request.args.get('action', 'add').lower()
    item_id_str = request.args.get('item_id')
    jwt = request.args.get('jwt')
    uid = request.args.get('uid')
    password = request.args.get('password')
    access_token = request.args.get('access_token')
    open_id = request.args.get('open_id')  # optional for access token method

    if not item_id_str or not item_id_str.isdigit():
        return "ERROR: Missing or invalid 'item_id' (must be integer)", 400
    item_id = int(item_id_str)

    
    if jwt:
        
        pass
    elif uid and password:
        jwt = get_jwt_from_guest(uid, password)
        if not jwt:
            return "ERROR: Failed to generate JWT from guest credentials", 401
    elif access_token:
        jwt = get_jwt_from_access_token(access_token, open_id)
        if not jwt:
            return "ERROR: Failed to generate JWT from access token", 401
    else:
        return "ERROR: Either 'jwt', 'uid+password', or 'access_token' is required", 400

    if action != 'add':
        return "ERROR: Unsupported action. Use 'add'.", 400

    success, status_code, error_msg = add_to_wishlist(jwt, item_id)
    if success:
        return f"ITEM ADDED SUCCESSFUL\nSTATUS {status_code} OK", 200
    else:
        return f"ERROR: Failed to add item (HTTP {status_code})\nDetails: {error_msg if error_msg else 'Server returned error'}", status_code

# -------------------- Main --------------------
