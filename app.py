import requests
import json
import threading
import time
import base64
import struct
import tempfile
import os
import sys
import importlib.util
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, request, render_template_string
import urllib3

try:
    from byte import Encrypt_ID, encrypt_api
except ImportError:
    def Encrypt_ID(uid: str) -> str:
        return uid.encode().hex()
    def encrypt_api(payload: str) -> str:
        return payload.encode().hex()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

REGION_MAP = {
    "ind": "https://client.ind.freefiremobile.com",
    "me": "https://clientbp.ggpolarbear.com",
    "vn": "https://clientbp.ggpolarbear.com",
    "bd": "https://clientbp.ggpolarbear.com",
    "pk": "https://clientbp.ggblueshark.com",
    "sg": "https://clientbp.ggpolarbear.com",
    "br": "https://client.us.freefiremobile.com",
    "na": "https://client.us.freefiremobile.com",
    "id": "https://clientbp.ggpolarbear.com",
    "ru": "https://clientbp.ggpolarbear.com",
    "th": "https://clientbp.ggpolarbear.com",
}

# ফ্ল্যাগ ইমোজি ম্যাপ
FLAG_MAP = {
    "ind": "🇮🇳",
    "me": "🇪🇬",
    "vn": "🇻🇳",
    "bd": "🇧🇩",
    "pk": "🇵🇰",
    "sg": "🇸🇬",
    "br": "🇧🇷",
    "na": "🇳🇦",
    "id": "🇮🇩",
    "ru": "🇷🇺",
    "th": "🇹🇭"
}

ALL_REGIONS = list(REGION_MAP.items())

OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
MAJOR_LOGIN_URL = "https://loginbp.ggblueshark.com/MajorLogin"
GET_LOGIN_DATA_URL_SUFFIX = "/GetLoginData"
CLIENT_ID = "100067"
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
PROTO_KEY = b'Yg&tc%DEuh6%Zc^8'
PROTO_IV = b'6oyZDr22E3ychjM%'

BASE_HEADERS = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB54"
}

MAJOR_LOGIN_REQ_B64 = "ChNNYWpvckxvZ2luUmVxLnByb3RvIvoKCgpNYWpvckxvZ2luEhIKCmV2ZW50X3RpbWUYAyABKAkSEQoJZ2FtZV9uYW1lGAQgASgJEhMKC3BsYXRmb3JtX2lkGAUgASgFEhYKDmNsaWVudF92ZXJzaW9uGAcgASgJEhcKD3N5c3RlbV9zb2Z0d2FyZRgIIAEoCRIXCg9zeXN0ZW1faGFyZHdhcmUYCSABKAkSGAoQdGVsZWNvbV9vcGVyYXRvchgKIAEoCRIUCgxuZXR3b3JrX3R5cGUYCyABKAkSFAoMc2NyZWVuX3dpZHRoGAwgASgNEhUKDXNjcmVlbl9oZWlnaHQYDSABKA0SEgoKc2NyZWVuX2RwaRgOIAEoCRIZChFwcm9jZXNzb3JfZGV0YWlscxgPIAEoCRIOCgZtZW1vcnkYECABKA0SFAoMZ3B1X3JlbmRlcmVyGBEgASgJEhMKC2dwdV92ZXJzaW9uGBIgASgJEhgKEHVuaXF1ZV9kZXZpY2VfaWQYEyABKAkSEQoJY2xpZW50X2lwGBQgASgJEhAKCGxhbmd1YWdlGBUgASgJEg8KB29wZW5faWQYFiABKAkSFAoMb3Blbl9pZF90eXBlGBcgASgJEhMKC2RldmljZV90eXBlGBggASgJEicKEG1lbW9yeV9hdmFpbGFibGUYGSABKAsyDS5HYW1lU2VjdXJpdHkSFAoMYWNjZXNzX3Rva2VuGB0gASgJEhcKD3BsYXRmb3JtX3Nka19pZBgeIAEoBRIaChJuZXR3b3JrX29wZXJhdG9yX2EYKSABKAkSFgoObmV0d29ya190eXBlX2EYKiABKAkSHAoUY2xpZW50X3VzaW5nX3ZlcnNpb24YOSABKAkSHgoWZXh0ZXJuYWxfc3RvcmFnZV90b3RhbBg8IAEoBRIiChpleHRlcm5hbF9zdG9yYWdlX2F2YWlsYWJsZRg9IAEoBRIeChZpbnRlcm5hbF9zdG9yYWdlX3RvdGFsGD4gASgFEiIKGmludGVybmFsX3N0b3JhZ2VfYXZhaWxhYmxlGD8gASgFEiMKG2dhbWVfZGlza19zdG9yYWdlX2F2YWlsYWJsZRhAIAEoBRIfChdnYW1lX2Rpc2tfc3RvcmFnZV90b3RhbBhBIAEoBRIlCh1leHRlcm5hbF9zZGNhcmRfYXZhaWxfc3RvcmFnZRhCIAEoBRIlCh1leHRlcm5hbF9zZGNhcmRfdG90YWxfc3RvcmFnZRhDIAEoBRIQCghsb2dpbl9ieRhJIAEoBRIUCgxsaWJyYXJ5X3BhdGgYSiABKAkSEgoKcmVnX2F2YXRhchhMIAEoBRIVCg1saWJyYXJ5X3Rva2VuGE0gASgJEhQKDGNoYW5uZWxfdHlwZRhOIAEoBRIQCghjcHVfdHlwZRhPIAEoBRIYChBjcHVfYXJjaGl0ZWN0dXJlGFEgASgJEhsKE2NsaWVudF92ZXJzaW9uX2NvZGUYUyABKAkSFAoMZ3JhcGhpY3NfYXBpGFYgASgJEh0KFXN1cHBvcnRlZF9hc3RjX2JpdHNldBhXIAEoDRIaChJsb2dpbl9vcGVuX2lkX3R5cGUYWCABKAUSGAoQYW5hbHl0aWNzX2RldGFpbBhZIAEoDBIUCgxsb2FkaW5nX3RpbWUYXCABKA0SFwoPcmVsZWFzZV9jaGFubmVsGF0gASgJEhIKCmV4dHJhX2luZm8YXiABKAkSIAoYYW5kcm9pZF9lbmdpbmVfaW5pdF9mbGFnGF8gASgNEg8KB2lmX3B1c2gYYSABKAUSDgoGaXNfdnBuGGIgASgFEhwKFG9yaWdpbl9wbGF0Zm9ybV90eXBlGGMgASgJEh0KFXByaW1hcnlfcGxhdGZvcm1fdHlwZRhkIAEoCSI1CgxHYW1lU2VjdXJpdHkSDwoHdmVyc2lvbhgGIAEoBRIUCgxoaWRkZW5fdmFsdWUYCCABKARiBnByb3RvMw=="
MAJOR_LOGIN_RES_B64 = "ChNNYWpvckxvZ2luUmVzLnByb3RvInwKDU1ham9yTG9naW5SZXMSEwoLYWNjb3VudF91aWQYASABKAQSDgoGcmVnaW9uGAIgASgJEg0KBXRva2VuGAggASgJEgsKA3VybBgKIAEoCRIRCgl0aW1lc3RhbXAYFSABKAMSCwoDa2V5GBYgASgMEgoKAml2GBcgASgMYgZwcm90bzM="
GET_LOGIN_DATA_B64 = "ChVHZXRMb2dpbkRhdGFSZXMucHJvdG8ipAEKDEdldExvZ2luRGF0YRISCgpBY2NvdW50VUlEGAEgASgEEg4KBlJlZ2lvbhgDIAEoCRITCgtBY2NvdW50TmFtZRgEIAEoCRIWCg5PbmxpbmVfSVBfUG9ydBgOIAEoCRIPCgdDbGFuX0lEGBQgASgDEhYKDkFjY291bnRJUF9Qb3J0GCAgASgJEhoKEkNsYW5fQ29tcGlsZWRfRGF0YRg3IAEoCWIGcHJvdG8z"

def load_protobuf_classes():
    classes = {}
    temp_dir = tempfile.mkdtemp()
    req_code = f'''
# -*- coding: utf-8 -*-
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(base64.b64decode("{MAJOR_LOGIN_REQ_B64}"))
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginReq_pb2', _globals)
'''
    res_code = f'''
# -*- coding: utf-8 -*-
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(base64.b64decode("{MAJOR_LOGIN_RES_B64}"))
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginRes_pb2', _globals)
'''
    data_code = f'''
# -*- coding: utf-8 -*-
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import base64
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(base64.b64decode("{GET_LOGIN_DATA_B64}"))
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'GetLoginDataRes_pb2', _globals)
'''
    req_path = os.path.join(temp_dir, 'MajorLoginReq_pb2.py')
    with open(req_path, 'w') as f:
        f.write(req_code)
    spec = importlib.util.spec_from_file_location("MajorLoginReq_pb2", req_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["MajorLoginReq_pb2"] = module
    spec.loader.exec_module(module)
    classes['MajorLogin'] = module.MajorLogin
    classes['GameSecurity'] = module.GameSecurity
    res_path = os.path.join(temp_dir, 'MajorLoginRes_pb2.py')
    with open(res_path, 'w') as f:
        f.write(res_code)
    spec = importlib.util.spec_from_file_location("MajorLoginRes_pb2", res_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["MajorLoginRes_pb2"] = module
    spec.loader.exec_module(module)
    classes['MajorLoginRes'] = module.MajorLoginRes
    data_path = os.path.join(temp_dir, 'GetLoginDataRes_pb2.py')
    with open(data_path, 'w') as f:
        f.write(data_code)
    spec = importlib.util.spec_from_file_location("GetLoginDataRes_pb2", data_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["GetLoginDataRes_pb2"] = module
    spec.loader.exec_module(module)
    classes['GetLoginData'] = module.GetLoginData
    return classes

PB = load_protobuf_classes()
MajorLogin = PB['MajorLogin']
GameSecurity = PB['GameSecurity']
MajorLoginRes = PB['MajorLoginRes']
GetLoginData = PB['GetLoginData']

def encrypt_proto(payload_bytes):
    cipher = AES.new(PROTO_KEY, AES.MODE_CBC, PROTO_IV)
    padded = pad(payload_bytes, AES.block_size)
    return cipher.encrypt(padded)

def decrypt_proto(encrypted_bytes):
    cipher = AES.new(PROTO_KEY, AES.MODE_CBC, PROTO_IV)
    decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    return decrypted

def generate_access_token(uid, password):
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/5.5.2P3(SM-A515F;Android 12;en-US;IND;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"
    }
    data = {
        "uid": uid, "password": password, "response_type": "token",
        "client_type": "2", "client_secret": CLIENT_SECRET, "client_id": CLIENT_ID
    }
    try:
        response = requests.post(OAUTH_URL, headers=headers, data=data, timeout=30, verify=False)
        if response.status_code == 200:
            resp_data = response.json()
            return resp_data.get("open_id"), resp_data.get("access_token"), None
        elif response.status_code == 429:
            return None, None, "Rate limited (429) - Too many requests"
        else:
            error_text = response.text[:200]
            return None, None, f"HTTP {response.status_code}: {error_text}"
    except Exception as e:
        return None, None, str(e)

def build_major_login_message(open_id, access_token):
    major_login = MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = "1.123.1"
    major_login.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "280"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    major_login.memory_available.version = 55
    major_login.memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2019118695"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWA0FUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    return major_login.SerializeToString()

def major_login(open_id, access_token):
    proto_payload = build_major_login_message(open_id, access_token)
    encrypted_payload = encrypt_proto(proto_payload)
    try:
        response = requests.post(MAJOR_LOGIN_URL, data=encrypted_payload, headers=BASE_HEADERS, timeout=30, verify=False)
        if response.status_code == 200:
            response_data = response.content
            if len(response_data) % 16 == 0:
                decrypted = decrypt_proto(response_data)
                if decrypted:
                    res = MajorLoginRes()
                    res.ParseFromString(decrypted)
                    return True, {
                        'account_uid': res.account_uid,
                        'region': res.region,
                        'token': res.token,
                        'url': res.url,
                        'timestamp': res.timestamp,
                        'key': res.key.hex() if res.key else None,
                        'iv': res.iv.hex() if res.iv else None
                    }
            res = MajorLoginRes()
            res.ParseFromString(response_data)
            if res.token:
                return True, {
                    'account_uid': res.account_uid,
                    'region': res.region,
                    'token': res.token,
                    'url': res.url,
                    'timestamp': res.timestamp,
                    'key': res.key.hex() if res.key else None,
                    'iv': res.iv.hex() if res.iv else None
                }
            return False, "No token in response"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def get_jwt_token(uid, password):
    open_id, access_token, err = generate_access_token(uid, password)
    if err:
        return None, err
    success, login_resp = major_login(open_id, access_token)
    if not success:
        return None, login_resp
    jwt_token = login_resp.get('token')
    if not jwt_token:
        return None, "No JWT token in MajorLogin response"
    return jwt_token, None

def send_friend_request(target_uid, token, region_server_url):
    try:
        encrypted_id = Encrypt_ID(target_uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)
        url = f"{region_server_url}/RequestAddingFriend"
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB54",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(encrypted_payload)//2),
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
            "Host": url.split('/')[2],
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate, br"
        }
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload), timeout=15)
        resp_text = response.text[:200]
        if response.status_code == 200:
            if "Invalid request body" in resp_text:
                return False, f"200 OK but body: {resp_text}", url
            return True, resp_text, url
        else:
            return False, f"HTTP {response.status_code}: {resp_text}", url
    except Exception as e:
        return False, str(e), region_server_url

# Global counters for terminal output
total_success = 0
total_failed = 0
lock = threading.Lock()

def process_account(account, target_uid, results, regions_to_try, delay=0):
    global total_success, total_failed
    if delay > 0:
        time.sleep(delay)
    uid = account['uid']
    password = account['password']
    token, err = get_jwt_token(uid, password)
    if not token:
        with lock:
            total_failed += 1
            results['failed'] += 1
            results['response_counts'][f"Token error: {err}"] = results['response_counts'].get(f"Token error: {err}", 0) + 1
        print(f"[FAIL] Account {uid} -> Token error: {err}")
        return
    success = False
    used_region_name = None
    final_response = None
    for region_name, server_url in regions_to_try:
        ok, resp_msg, used_url = send_friend_request(target_uid, token, server_url)
        if ok:
            success = True
            used_region_name = region_name
            final_response = resp_msg
            break
        else:
            final_response = resp_msg
    with lock:
        if success:
            total_success += 1
            results['success'] += 1
            results['region_names'].add(used_region_name)  # region name যোগ করছি
            results['response_counts'][final_response] = results['response_counts'].get(final_response, 0) + 1
            print(f"[SUCCESS] Account {uid} -> Friend request sent to {target_uid} via {used_region_name.upper()}")
        else:
            total_failed += 1
            results['failed'] += 1
            results['response_counts'][final_response] = results['response_counts'].get(final_response, 0) + 1
            print(f"[FAIL] Account {uid} -> {final_response}")

def load_accounts():
    accounts = []
    try:
        with open("accounts.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                uid, pwd = line.split(':', 1)
                accounts.append({"uid": uid, "password": pwd})
        return accounts
    except FileNotFoundError:
        return []
    except Exception:
        return []

def spam_friend_requests(target_uid, region=None):
    global total_success, total_failed
    total_success = 0
    total_failed = 0
    accounts = load_accounts()
    if not accounts:
        return {"error": "No accounts found in accounts.txt"}, 404
    accounts_to_use = accounts

    if region:
        region_lower = region.lower()
        if region_lower in REGION_MAP:
            regions_to_try = [(region_lower, REGION_MAP[region_lower])]
        else:
            return {"error": f"Invalid region: {region}"}, 400
    else:
        regions_to_try = ALL_REGIONS

    results = {
        "success": 0,
        "failed": 0,
        "region_names": set(),   # region নাম সংরক্ষণ
        "response_counts": {}
    }

    threads = []
    thread_delay = 0.1
    for i, acc in enumerate(accounts_to_use):
        t = threading.Thread(target=process_account, args=(acc, target_uid, results, regions_to_try, i * thread_delay))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    results["region_names"] = list(results["region_names"])
    results["total_accounts_available"] = len(accounts)
    results["accounts_used"] = len(accounts_to_use)
    return results

# ============================================================
#  UI LAYER — professional dark theme, animated flags, control panel + JSON API
#  (Backend logic above is untouched)
# ============================================================
from flask import jsonify, redirect, url_for

FLAG_CDN = "https://flagcdn.com/w80/{code}.png"
# ISO codes for the flag CDN (na has no ISO region so falls back to a plain shield)
FLAG_ISO = {
    "ind": "in", "me": "me", "vn": "vn", "bd": "bd", "pk": "pk",
    "sg": "sg", "br": "br", "na": "na", "id": "id", "ru": "ru", "th": "th",
}
REGION_LABEL = {
    "ind": "India", "me": "Middle East", "vn": "Vietnam", "bd": "Bangladesh",
    "pk": "Pakistan", "sg": "Singapore", "br": "Brazil", "na": "North America",
    "id": "Indonesia", "ru": "Russia", "th": "Thailand",
}

LOGO_DATA_URI = "data:image/webp;base64,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"

SHARED_STYLE = """
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{overflow-x:hidden}
body{
  font-family:'Inter','Segoe UI',system-ui,sans-serif;
  min-height:100vh;color:#e6ebf5;background:#04060c;position:relative;
  display:flex;justify-content:center;align-items:flex-start;
  padding:56px 20px 80px;
}

/* ============== LIVE WALLPAPER ============== */
.bg{position:fixed;inset:0;z-index:-4;overflow:hidden;
  background:linear-gradient(-45deg,#04060c,#0a0f24,#1a0533,#04101c,#180a2e,#04060c);
  background-size:500% 500%;animation:bgShift 22s ease infinite}
@keyframes bgShift{0%{background-position:0% 50%}25%{background-position:100% 20%}50%{background-position:80% 100%}75%{background-position:20% 80%}100%{background-position:0% 50%}}

/* aurora sweep */
.aurora{position:fixed;inset:-20%;z-index:-3;pointer-events:none;
  background:
    radial-gradient(60% 40% at 20% 30%,rgba(139,92,246,.35),transparent 60%),
    radial-gradient(55% 40% at 80% 60%,rgba(59,130,246,.32),transparent 60%),
    radial-gradient(50% 35% at 50% 90%,rgba(236,72,153,.28),transparent 60%);
  filter:blur(60px);animation:auroraDrift 20s ease-in-out infinite alternate}
@keyframes auroraDrift{0%{transform:translate(0,0) rotate(0)}100%{transform:translate(-6%,4%) rotate(6deg)}}

/* moving color orbs */
.orb{position:fixed;border-radius:50%;filter:blur(90px);opacity:.55;z-index:-2;pointer-events:none;mix-blend-mode:screen}
.orb.o1{width:520px;height:520px;background:#3b82f6;top:-120px;left:-120px;animation:float1 16s ease-in-out infinite}
.orb.o2{width:460px;height:460px;background:#a855f7;top:30%;right:-140px;animation:float2 20s ease-in-out infinite}
.orb.o3{width:400px;height:400px;background:#06b6d4;bottom:-140px;left:20%;animation:float3 24s ease-in-out infinite}
.orb.o4{width:340px;height:340px;background:#ec4899;top:60%;left:35%;animation:float1 22s ease-in-out infinite reverse}
@keyframes float1{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(180px,120px) scale(1.15)}}
@keyframes float2{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-200px,140px) scale(1.2)}}
@keyframes float3{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(140px,-160px) scale(1.1)}}

/* grid overlay */
.grid-bg{position:fixed;inset:0;z-index:-1;pointer-events:none;
  background:
    linear-gradient(rgba(120,160,255,.06) 1px,transparent 1px) 0 0/48px 48px,
    linear-gradient(90deg,rgba(120,160,255,.06) 1px,transparent 1px) 0 0/48px 48px;
  mask-image:radial-gradient(ellipse at center,#000 40%,transparent 85%);
  animation:pan 30s linear infinite}
@keyframes pan{to{background-position:480px 480px,480px 480px}}

/* rising particles */
.particles{position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none}
.particles i{position:absolute;bottom:-20px;width:6px;height:6px;border-radius:50%;
  background:radial-gradient(circle,#8ab4ff,transparent 70%);opacity:.7;animation:rise linear infinite;
  box-shadow:0 0 10px currentColor}
.particles i:nth-child(1){left:5%;animation-duration:14s;animation-delay:0s;color:#8ab4ff}
.particles i:nth-child(2){left:15%;animation-duration:18s;animation-delay:2s;color:#c4a3ff;background:radial-gradient(circle,#c4a3ff,transparent 70%)}
.particles i:nth-child(3){left:28%;animation-duration:12s;animation-delay:4s;color:#8ab4ff}
.particles i:nth-child(4){left:40%;animation-duration:20s;animation-delay:1s;color:#7ff3ff;background:radial-gradient(circle,#7ff3ff,transparent 70%)}
.particles i:nth-child(5){left:52%;animation-duration:16s;animation-delay:5s;color:#8ab4ff}
.particles i:nth-child(6){left:63%;animation-duration:22s;animation-delay:3s;color:#ffb8e0;background:radial-gradient(circle,#ffb8e0,transparent 70%)}
.particles i:nth-child(7){left:75%;animation-duration:15s;animation-delay:6s;color:#8ab4ff}
.particles i:nth-child(8){left:88%;animation-duration:19s;animation-delay:2s;color:#c4a3ff;background:radial-gradient(circle,#c4a3ff,transparent 70%)}
.particles i:nth-child(9){left:95%;animation-duration:13s;animation-delay:4s;color:#8ab4ff}
.particles i:nth-child(10){left:34%;animation-duration:17s;animation-delay:7s;color:#7ff3ff;background:radial-gradient(circle,#7ff3ff,transparent 70%)}
.particles i:nth-child(11){left:70%;animation-duration:21s;animation-delay:8s;color:#ffb8e0;background:radial-gradient(circle,#ffb8e0,transparent 70%)}
.particles i:nth-child(12){left:82%;animation-duration:14s;animation-delay:1.5s;color:#8ab4ff}
@keyframes rise{0%{transform:translateY(0) scale(.6);opacity:0}
  10%{opacity:.9}90%{opacity:.5}100%{transform:translateY(-105vh) scale(1.4);opacity:0}}

/* shooting stars */
.stars{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
.stars b{position:absolute;width:2px;height:2px;background:#fff;border-radius:50%;
  box-shadow:0 0 12px #fff,-40px -20px 0 -1px #fff,-80px -40px 0 -1px #fff;
  opacity:0;animation:shoot 6s linear infinite}
.stars b:nth-child(1){top:15%;left:-10%;animation-delay:0s}
.stars b:nth-child(2){top:35%;left:-10%;animation-delay:2.4s}
.stars b:nth-child(3){top:60%;left:-10%;animation-delay:4.2s}
@keyframes shoot{0%{transform:translate(0,0);opacity:0}
  8%{opacity:1}60%{opacity:1}100%{transform:translate(120vw,60vh);opacity:0}}

/* ============== container ============== */
.wrap{position:relative;width:100%;max-width:960px;animation:fadeUp .8s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.card-shell{position:relative;
  background:linear-gradient(180deg,rgba(18,22,34,.78),rgba(10,13,22,.82));
  border:1px solid rgba(255,255,255,.07);border-radius:22px;padding:38px 36px;
  box-shadow:0 30px 90px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.05);
  backdrop-filter:blur(18px);overflow:hidden}
.card-shell::before{content:"";position:absolute;inset:-2px;border-radius:24px;padding:2px;z-index:-1;
  background:conic-gradient(from 0deg,#3b82f6,#a855f7,#06b6d4,#ec4899,#3b82f6);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);
  -webkit-mask-composite:xor;mask-composite:exclude;opacity:.5;animation:spin 8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

.brand{display:flex;align-items:center;gap:14px;margin-bottom:6px}
.brand .mark{width:46px;height:46px;border-radius:14px;position:relative;overflow:hidden;
  background:conic-gradient(from 0deg,#3b82f6,#8b5cf6,#22d3ee,#ec4899,#3b82f6);
  box-shadow:0 6px 24px rgba(139,92,246,.5),0 0 0 1px rgba(255,255,255,.08);animation:spin 6s linear infinite}
.brand .mark::after{content:"J";position:absolute;inset:2px;border-radius:12px;display:grid;place-items:center;
  font-weight:800;font-family:'Space Grotesk',sans-serif;color:#f4f6fb;font-size:1.3rem;background:#0b0f1a;animation:spin 6s linear infinite reverse}
.brand .name{font-family:'Space Grotesk',sans-serif;font-weight:700;letter-spacing:.5px;font-size:1.05rem;color:#f4f6fb}
.brand .name span{color:#8ea3c7;font-weight:500;margin-left:8px;font-size:.85rem;letter-spacing:2px;text-transform:uppercase}

h1.title{font-family:'Space Grotesk',sans-serif;font-size:2.4rem;font-weight:700;
  letter-spacing:-.5px;margin-top:18px;color:#f4f6fb;line-height:1.1}
h1.title .accent{background:linear-gradient(90deg,#60a5fa,#a78bfa,#22d3ee,#ec4899,#60a5fa);
  -webkit-background-clip:text;background-clip:text;color:transparent;
  background-size:300% auto;animation:sheen 5s linear infinite}
@keyframes sheen{to{background-position:300% 0}}
.subtitle{color:#8ea3c7;font-size:.95rem;margin-top:8px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 4px rgba(34,197,94,.15);animation:pulse 1.6s ease-in-out infinite}
@keyframes pulse{50%{transform:scale(1.4);opacity:.55;box-shadow:0 0 0 8px rgba(34,197,94,0)}}

.section{margin-top:24px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);
  border-radius:16px;padding:22px 24px;animation:fadeUp .8s ease}
.section h3{font-family:'Space Grotesk',sans-serif;font-size:.85rem;letter-spacing:2.5px;
  text-transform:uppercase;color:#8ea3c7;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.section h3::before{content:"";width:6px;height:6px;border-radius:50%;background:#60a5fa;box-shadow:0 0 12px #60a5fa;animation:pulse 1.8s ease-in-out infinite}

.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.stat{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.05);border-radius:12px;
  padding:14px 16px;display:flex;justify-content:space-between;align-items:center;transition:.25s}
.stat:hover{border-color:rgba(96,165,250,.4);transform:translateY(-2px);background:rgba(96,165,250,.05)}
.stat .k{color:#8ea3c7;font-size:.82rem;letter-spacing:.4px}
.stat .v{font-weight:700;font-size:1.3rem;font-family:'Space Grotesk',sans-serif}
.v.ok{color:#4ade80}.v.err{color:#f87171}.v.hi{color:#60a5fa}

/* ============== CLICKABLE REGION CARDS ============== */
.region-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.region-card{position:relative;display:flex;align-items:center;gap:12px;
  padding:12px 14px;border-radius:14px;cursor:pointer;text-decoration:none;
  background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.08);
  transition:transform .3s cubic-bezier(.2,.9,.25,1.2), box-shadow .3s, border-color .3s, background .3s;
  animation:riseIn .6s ease both;overflow:hidden}
.region-card:hover{transform:translateY(-4px) scale(1.03);border-color:rgba(96,165,250,.5);
  background:rgba(96,165,250,.08);box-shadow:0 14px 34px -14px rgba(96,165,250,.55)}
.region-card::before{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent,rgba(255,255,255,.14),transparent);
  transform:translateX(-120%);transition:transform .7s}
.region-card:hover::before{transform:translateX(120%)}
.region-card.active{background:linear-gradient(135deg,rgba(168,85,247,.25),rgba(59,130,246,.18));
  border-color:rgba(168,85,247,.7);box-shadow:0 0 0 2px rgba(168,85,247,.35),0 16px 40px -12px rgba(168,85,247,.55)}
.region-card.active::after{content:"";position:absolute;top:8px;right:8px;width:9px;height:9px;border-radius:50%;
  background:#a855f7;box-shadow:0 0 12px #a855f7;animation:pulse 1.5s ease-in-out infinite}
.region-card .label{font-weight:700;font-size:.92rem;color:#f4f6fb;letter-spacing:.2px}
.region-card .code{color:#8ea3c7;font-size:.65rem;letter-spacing:2px;text-transform:uppercase;margin-top:2px}
@keyframes riseIn{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}

/* animated waving flags */
.flags{display:flex;flex-wrap:wrap;gap:14px}
.flag-chip{display:flex;align-items:center;gap:12px;padding:8px 16px 8px 8px;border-radius:999px;
  background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.08);transition:.3s}
.flag-chip:hover{border-color:rgba(96,165,250,.45);transform:translateY(-3px) scale(1.03);
  box-shadow:0 8px 20px rgba(96,165,250,.15)}
.flag-chip .label{font-weight:600;font-size:.9rem;color:#e6ebf5;letter-spacing:.3px}
.flag-chip .code{color:#8ea3c7;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;margin-left:2px}

.flag{width:46px;height:32px;border-radius:5px;overflow:hidden;position:relative;
  box-shadow:0 4px 14px rgba(0,0,0,.5),inset 0 0 0 1px rgba(255,255,255,.1);perspective:260px}
.flag img{width:100%;height:100%;object-fit:cover;display:block;
  animation:wave 2.6s ease-in-out infinite;transform-origin:left center;
  filter:drop-shadow(0 2px 6px rgba(0,0,0,.4))}
.flag::before{content:"";position:absolute;inset:0;pointer-events:none;z-index:2;
  background:repeating-linear-gradient(90deg,transparent 0 8px,rgba(0,0,0,.12) 8px 10px,transparent 10px 18px);
  mix-blend-mode:overlay;animation:waveMask 2.6s ease-in-out infinite}
.flag::after{content:"";position:absolute;inset:0;pointer-events:none;z-index:3;
  background:linear-gradient(100deg,rgba(255,255,255,.5) 0%,transparent 30%,transparent 70%,rgba(0,0,0,.35) 100%);
  mix-blend-mode:overlay;animation:shine 3s ease-in-out infinite}
@keyframes wave{
  0%,100%{transform:skewX(-10deg) skewY(3deg) rotateY(-6deg) translateX(0)}
  25%{transform:skewX(8deg) skewY(-3deg) rotateY(6deg) translateX(2px)}
  50%{transform:skewX(10deg) skewY(3deg) rotateY(-3deg) translateX(0)}
  75%{transform:skewX(-8deg) skewY(-2deg) rotateY(3deg) translateX(-2px)}
}
@keyframes waveMask{
  0%,100%{transform:translateX(-4px) skewY(1deg)}
  50%{transform:translateX(4px) skewY(-1deg)}
}
@keyframes shine{0%,100%{transform:translateX(-14px)}50%{transform:translateX(14px)}}

table.resp{width:100%;border-collapse:collapse;font-size:.9rem}
table.resp th{text-align:left;color:#8ea3c7;font-weight:500;font-size:.72rem;
  letter-spacing:2px;text-transform:uppercase;padding:10px 8px;border-bottom:1px solid rgba(255,255,255,.06)}
table.resp td{padding:12px 8px;color:#d5dcec;border-bottom:1px solid rgba(255,255,255,.04);word-break:break-word}
table.resp tr{transition:.2s}
table.resp tr:hover td{background:rgba(96,165,250,.05)}
.badge{display:inline-block;padding:3px 12px;border-radius:999px;font-size:.75rem;font-weight:600;letter-spacing:.3px}
.badge.s{background:rgba(74,222,128,.12);color:#4ade80;border:1px solid rgba(74,222,128,.25)}
.badge.f{background:rgba(248,113,113,.12);color:#f87171;border:1px solid rgba(248,113,113,.25)}

.footer{margin-top:32px;padding-top:22px;border-top:1px solid rgba(255,255,255,.06);
  display:flex;flex-direction:column;gap:16px;align-items:center}
.btn-row{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}
.btn{position:relative;display:inline-flex;align-items:center;gap:8px;
  padding:12px 24px;border-radius:11px;text-decoration:none;font-weight:600;font-size:.9rem;
  letter-spacing:.4px;cursor:pointer;border:1px solid transparent;transition:.3s;overflow:hidden}
.btn.primary{background:linear-gradient(135deg,#3b82f6,#8b5cf6,#ec4899);background-size:200% auto;
  color:#fff;box-shadow:0 8px 26px rgba(139,92,246,.4);animation:btnShift 4s ease infinite,pulseGlow 2.6s ease-in-out infinite}
@keyframes btnShift{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
@keyframes pulseGlow{0%,100%{box-shadow:0 8px 26px rgba(139,92,246,.4)}50%{box-shadow:0 8px 40px rgba(236,72,153,.7)}}
.btn.primary:hover{transform:translateY(-3px);box-shadow:0 14px 34px rgba(236,72,153,.5)}
.btn.ghost{background:rgba(255,255,255,.04);color:#e6ebf5;border-color:rgba(255,255,255,.1)}
.btn.ghost:hover{background:rgba(255,255,255,.08);border-color:#60a5fa;transform:translateY(-2px)}
.btn.tg{background:linear-gradient(135deg,#0088cc,#00b4ff);color:#fff;box-shadow:0 8px 24px rgba(0,180,255,.35)}
.btn.tg:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(0,180,255,.5)}
.btn::after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent,rgba(255,255,255,.28),transparent);
  transform:translateX(-120%);transition:transform .7s}
.btn:hover::after{transform:translateX(120%)}
.credit{color:#5a6786;font-size:.8rem;letter-spacing:.4px;text-align:center}
.credit b{color:#8ea3c7;font-weight:600}

.form-row{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:end}
.input,.select{width:100%;padding:12px 14px;border-radius:10px;
  background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  color:#e6ebf5;font-size:.95rem;font-family:inherit;transition:.2s}
.input:focus,.select:focus{outline:none;border-color:#a855f7;background:rgba(168,85,247,.06);box-shadow:0 0 0 3px rgba(168,85,247,.18)}
.field-label{display:block;color:#8ea3c7;font-size:.72rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.api-box{background:#0b0f1a;border:1px solid rgba(255,255,255,.06);border-radius:10px;
  padding:14px 16px;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:.82rem;color:#a3b3d1;word-break:break-all}
.api-box b{color:#60a5fa}
.hint{color:#8ea3c7;font-size:.82rem;margin-top:8px}
.selected-tag{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:999px;
  background:rgba(168,85,247,.15);border:1px solid rgba(168,85,247,.4);color:#c4a3ff;font-size:.78rem;font-weight:600}

/* ============== LOADING OVERLAY ============== */
.loader-overlay{position:fixed;inset:0;background:rgba(4,6,12,.85);backdrop-filter:blur(14px);
  display:none;align-items:center;justify-content:center;z-index:9999;flex-direction:column;gap:24px;
  animation:fadeIn .3s ease}
.loader-overlay.on{display:flex}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.loader-ring{width:110px;height:110px;position:relative}
.loader-ring::before,.loader-ring::after{content:"";position:absolute;inset:0;border-radius:50%;
  border:3px solid transparent}
.loader-ring::before{border-top-color:#a855f7;border-right-color:#60a5fa;animation:spin 1.2s linear infinite;
  box-shadow:0 0 30px rgba(168,85,247,.5)}
.loader-ring::after{inset:16px;border-bottom-color:#ec4899;border-left-color:#22d3ee;animation:spin 1.6s linear infinite reverse;
  box-shadow:0 0 20px rgba(236,72,153,.4)}
.loader-core{position:absolute;inset:32px;border-radius:50%;
  background:conic-gradient(from 0deg,#a855f7,#60a5fa,#22d3ee,#ec4899,#a855f7);
  animation:spin 3s linear infinite;filter:blur(2px);opacity:.9}
.loader-text{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;letter-spacing:3px;
  text-transform:uppercase;background:linear-gradient(90deg,#a855f7,#60a5fa,#ec4899,#a855f7);
  background-size:200% auto;-webkit-background-clip:text;background-clip:text;color:transparent;
  animation:sheen 2.5s linear infinite}
.loader-dots{display:flex;gap:8px}
.loader-dots span{width:8px;height:8px;border-radius:50%;background:#a855f7;
  animation:bounce 1.4s ease-in-out infinite;box-shadow:0 0 10px #a855f7}
.loader-dots span:nth-child(2){background:#60a5fa;box-shadow:0 0 10px #60a5fa;animation-delay:.2s}
.loader-dots span:nth-child(3){background:#ec4899;box-shadow:0 0 10px #ec4899;animation-delay:.4s}
@keyframes bounce{0%,80%,100%{transform:scale(.6);opacity:.5}40%{transform:scale(1.2);opacity:1}}


/* ============== PAGE PRELOADER ============== */
#preloader{position:fixed;inset:0;z-index:99999;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:26px;background:radial-gradient(circle at 50% 45%,#0d1226,#04060c 70%);
  transition:opacity .7s ease,visibility .7s ease}
#preloader.done{opacity:0;visibility:hidden}
.pl-logo{position:relative;width:170px;height:170px;display:grid;place-items:center;animation:plPop 1s cubic-bezier(.2,.9,.25,1.4) both}
@keyframes plPop{0%{opacity:0;transform:scale(.5) rotate(-14deg)}100%{opacity:1;transform:scale(1) rotate(0)}}
.pl-logo img{width:112px;height:112px;border-radius:50%;object-fit:cover;position:relative;z-index:3;
  box-shadow:0 0 40px rgba(255,196,0,.5),0 0 90px rgba(168,85,247,.35);animation:logoBreathe 3s ease-in-out infinite}
@keyframes logoBreathe{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
.pl-logo::before,.pl-logo::after{content:"";position:absolute;border-radius:50%}
.pl-logo::before{inset:0;border:2px solid transparent;border-top-color:#ffc400;border-right-color:#a855f7;
  animation:spin 1.6s linear infinite;filter:drop-shadow(0 0 10px rgba(255,196,0,.7))}
.pl-logo::after{inset:16px;border:2px dashed rgba(96,165,250,.55);animation:spin 4s linear infinite reverse}
.pl-name{font-family:'Space Grotesk',sans-serif;font-weight:700;letter-spacing:8px;font-size:1.15rem;
  text-transform:uppercase;background:linear-gradient(90deg,#ffd76a,#fff,#a855f7,#60a5fa,#ffd76a);
  background-size:300% auto;-webkit-background-clip:text;background-clip:text;color:transparent;animation:sheen 3s linear infinite}
.pl-bar{width:210px;height:4px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden}
.pl-bar i{display:block;height:100%;width:0;border-radius:99px;
  background:linear-gradient(90deg,#ffc400,#a855f7,#60a5fa);box-shadow:0 0 14px rgba(168,85,247,.8);
  animation:plLoad 2.1s cubic-bezier(.4,0,.2,1) forwards}
@keyframes plLoad{0%{width:0}55%{width:72%}100%{width:100%}}
.pl-tip{color:#7d8db0;font-size:.75rem;letter-spacing:3px;text-transform:uppercase;animation:blinkSoft 1.6s ease-in-out infinite}
@keyframes blinkSoft{50%{opacity:.35}}

/* ============== HERO CHANNEL LOGO ============== */
.hero{display:flex;flex-direction:column;align-items:center;gap:14px;margin:6px 0 4px;text-align:center}
.logo-wrap{position:relative;width:150px;height:150px;display:grid;place-items:center;
  animation:floatY 5s ease-in-out infinite}
@keyframes floatY{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.logo-wrap img{width:112px;height:112px;border-radius:50%;object-fit:cover;z-index:3;position:relative;
  box-shadow:0 0 32px rgba(255,196,0,.45),0 0 70px rgba(168,85,247,.3),0 0 0 3px rgba(255,214,106,.35);
  transition:transform .5s cubic-bezier(.2,.9,.25,1.4)}
.logo-wrap:hover img{transform:scale(1.08) rotate(4deg)}
.logo-wrap .ring{position:absolute;border-radius:50%;pointer-events:none}
.logo-wrap .r1{inset:0;border:2px solid transparent;border-top-color:#ffc400;border-left-color:#a855f7;animation:spin 5s linear infinite}
.logo-wrap .r2{inset:12px;border:1px dashed rgba(96,165,250,.5);animation:spin 9s linear infinite reverse}
.logo-wrap .halo{position:absolute;inset:-18px;border-radius:50%;z-index:0;
  background:conic-gradient(from 0deg,rgba(255,196,0,.45),rgba(168,85,247,.4),rgba(34,211,238,.35),rgba(255,196,0,.45));
  filter:blur(24px);animation:spin 7s linear infinite,haloPulse 3.4s ease-in-out infinite}
@keyframes haloPulse{0%,100%{opacity:.55}50%{opacity:1}}
.logo-wrap .spark{position:absolute;width:6px;height:6px;border-radius:50%;background:#ffd76a;
  box-shadow:0 0 12px #ffd76a;top:50%;left:50%;margin:-3px;animation:orbit 6s linear infinite}
.logo-wrap .spark.s2{background:#a855f7;box-shadow:0 0 12px #a855f7;animation-duration:8s;animation-delay:-2s}
.logo-wrap .spark.s3{background:#60a5fa;box-shadow:0 0 12px #60a5fa;animation-duration:10s;animation-delay:-5s}
@keyframes orbit{to{transform:rotate(360deg) translateX(78px) rotate(-360deg)}}
.hero .ch-name{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.5rem;letter-spacing:2px;
  background:linear-gradient(90deg,#ffd76a,#fff7d6,#ffc400,#fff,#ffd76a);background-size:300% auto;
  -webkit-background-clip:text;background-clip:text;color:transparent;animation:sheen 4s linear infinite;
  text-shadow:0 0 30px rgba(255,196,0,.25)}
.hero .ch-tag{color:#8ea3c7;font-size:.82rem;letter-spacing:4px;text-transform:uppercase}

/* typing line */
.type-line{font-family:'JetBrains Mono',monospace;font-size:.92rem;color:#a9bbdd;min-height:22px}
.type-line .cursor{display:inline-block;width:9px;background:#a855f7;margin-left:2px;
  box-shadow:0 0 10px #a855f7;animation:caret .8s steps(1) infinite}
@keyframes caret{50%{opacity:0}}

/* scroll reveal */
.reveal{opacity:0;transform:translateY(28px) scale(.98);transition:opacity .8s cubic-bezier(.2,.9,.25,1),transform .8s cubic-bezier(.2,.9,.25,1)}
.reveal.in{opacity:1;transform:none}

/* premium boxes */
.section{position:relative;overflow:hidden;transition:border-color .4s,box-shadow .4s,transform .4s}
.section::after{content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.07),transparent);
  transform:skewX(-18deg);animation:boxSweep 7s ease-in-out infinite}
@keyframes boxSweep{0%{left:-60%}45%{left:130%}100%{left:130%}}
.section:hover{border-color:rgba(168,85,247,.35);box-shadow:0 20px 60px -28px rgba(168,85,247,.55);transform:translateY(-3px)}
.stat{position:relative;overflow:hidden}
.stat::after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent,rgba(255,255,255,.1),transparent);
  transform:translateX(-130%);transition:transform .8s}
.stat:hover::after{transform:translateX(130%)}
html{scroll-behavior:smooth}
::selection{background:rgba(168,85,247,.4);color:#fff}
::-webkit-scrollbar{width:10px}
::-webkit-scrollbar-track{background:#070a13}
::-webkit-scrollbar-thumb{border-radius:99px;background:linear-gradient(#a855f7,#3b82f6)}

/* loader logo */
.loader-logo{width:64px;height:64px;border-radius:50%;object-fit:cover;position:absolute;inset:23px;
  box-shadow:0 0 26px rgba(255,196,0,.6);animation:logoBreathe 2s ease-in-out infinite;z-index:4}
.loader-ring{filter:drop-shadow(0 0 18px rgba(168,85,247,.5))}

@media(max-width:640px){
  .card-shell{padding:26px 20px}
  h1.title{font-size:1.7rem}
  .grid{grid-template-columns:1fr}
  .form-row{grid-template-columns:1fr}
  .region-grid{grid-template-columns:repeat(2,1fr)}
  .logo-wrap{width:126px;height:126px}
  .logo-wrap img{width:92px;height:92px}
  .hero .ch-name{font-size:1.2rem}
}
</style>
"""

WALLPAPER = """
<div class="bg"></div>
<div class="aurora"></div>
<div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div><div class="orb o4"></div>
<div class="grid-bg"></div>
<div class="stars"><b></b><b></b><b></b></div>
<div class="particles"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
"""


PRELOADER = """
<div id="preloader">
  <div class="pl-logo"><img src='""" + LOGO_DATA_URI + """' alt="JAHID EMPIRE"></div>
  <div class="pl-name">Jahid X Empire</div>
  <div class="pl-bar"><i></i></div>
  <div class="pl-tip">Initializing premium panel</div>
</div>
"""

HERO = """
<div class="hero reveal">
  <div class="logo-wrap">
    <div class="halo"></div>
    <span class="ring r1"></span><span class="ring r2"></span>
    <span class="spark s1"></span><span class="spark s2"></span><span class="spark s3"></span>
    <img src='""" + LOGO_DATA_URI + """' alt="JAHID EMPIRE logo">
  </div>
  <div class="ch-name">JAHID X EMPIRE</div>
  <div class="ch-tag"></div>
  <div class="type-line"><span id="typeTarget"></span><span class="cursor">&nbsp;</span></div>
</div>
"""

LOADER_BOX = """
<div class="loader-overlay" id="loader">
  <div class="loader-ring"><div class="loader-core"></div>
    <img class="loader-logo" src='""" + LOGO_DATA_URI + """' alt="logo"></div>
  <div class="loader-text">Launching Request</div>
  <div class="loader-dots"><span></span><span></span><span></span></div>
</div>
"""

FX_SCRIPT = """
<script>
(function(){
  var pl=document.getElementById('preloader');
  function hide(){ if(pl){ setTimeout(function(){pl.classList.add('done');},2100); } }
  if(document.readyState==='complete') hide(); else window.addEventListener('load',hide);

  var lines=['> Secure tunnel established...','> SET TARGET UID ...','> Select a server and launch \\u26a1','> Powered by JAHID X EMPIRE'];
  var t=document.getElementById('typeTarget');
  if(t){
    var li=0,ci=0,del=false;
    (function tick(){
      var cur=lines[li];
      t.textContent = del ? cur.slice(0,ci--) : cur.slice(0,ci++);
      var d = del?28:52;
      if(!del && ci>cur.length){ del=true; d=1500; }
      if(del && ci<0){ del=false; ci=0; li=(li+1)%lines.length; d=350; }
      setTimeout(tick,d);
    })();
  }

  var io=new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); } });
  },{threshold:.12});
  document.querySelectorAll('.section,.hero,.footer').forEach(function(el,i){
    el.classList.add('reveal'); el.style.transitionDelay=(i*70)+'ms'; io.observe(el);
  });

  document.querySelectorAll('.section').forEach(function(card){
    card.addEventListener('mousemove',function(e){
      var r=card.getBoundingClientRect();
      var x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
      card.style.transform='perspective(900px) rotateY('+(x*4)+'deg) rotateX('+(-y*4)+'deg) translateY(-3px)';
    });
    card.addEventListener('mouseleave',function(){ card.style.transform=''; });
  });
})();
</script>
"""

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JXE FRIEND REQ SPAM — Report</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
""" + SHARED_STYLE + """
</head><body>
""" + WALLPAPER + """

""" + PRELOADER + LOADER_BOX + """
<div class="wrap"><div class="card-shell">
  <div class="brand">
    <div class="mark"></div>
    <div class="name">JXE<span> · Report</span></div>
  </div>
""" + HERO + """
  <h1 class="title" style="text-align:center">JXE <span class="accent">FRIEND REQ SPAM</span></h1>
  <div class="subtitle">
    <span>Target UID: <b style="color:#f4f6fb">{{ target_uid }}</b></span>
    <span style="opacity:.4">•</span>
    <span class="dot"></span><span style="color:#4ade80">Completed</span>
    <span style="opacity:.4">•</span>
    <span>{{ timestamp }}</span>
  </div>

  <div class="section">
    <h3>Summary</h3>
    <div class="grid">
      <div class="stat"><span class="k">Accounts Used</span><span class="v hi">{{ data.accounts_used }}</span></div>
      <div class="stat"><span class="k">Success</span><span class="v ok">{{ data.success }}</span></div>
      <div class="stat"><span class="k">Failed</span><span class="v err">{{ data.failed }}</span></div>
      <div class="stat"><span class="k">Available Pool</span><span class="v">{{ data.total_accounts_available }}</span></div>
    </div>
  </div>

  <div class="section">
    <h3>Servers Used</h3>
    <div class="flags">
      {% for region in data.region_names %}
      <div class="flag-chip">
        <div class="flag"><img src="https://flagcdn.com/w80/{{ flag_iso.get(region, region) }}.png" alt="{{ region }}"></div>
        <div><div class="label">{{ region_label.get(region, region.upper()) }}</div><div class="code">{{ region }}</div></div>
      </div>
      {% else %}
      <div style="color:#5a6786">No server recorded.</div>
      {% endfor %}
    </div>
  </div>

  <div class="section">
    <h3>Response Breakdown</h3>
    <table class="resp">
      <thead><tr><th>Response</th><th style="width:100px">Count</th></tr></thead><tbody>
      {% for resp, count in data.response_counts.items() %}
      <tr><td>{{ resp[:120] }}{% if resp|length > 120 %}…{% endif %}</td>
      <td><span class="badge {% if 'SUCCESS' in resp or 'sent' in resp %}s{% else %}f{% endif %}">{{ count }}</span></td></tr>
      {% else %}
      <tr><td colspan="2" style="color:#5a6786">No responses.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="footer">
    <div class="btn-row">
      <a href="/" class="btn ghost">← New Request</a>
      <a href="https://t.me/Jahid_x_Empire" target="_blank" class="btn tg"><span style="width:8px;height:8px;border-radius:50%;background:#fff;box-shadow:0 0 8px #fff;animation:pulse 1.6s ease-in-out infinite"></span>Join Channel</a>
      <a href="https://t.me/Itz_Jahid_X" target="_blank" class="btn primary">Contact Owner</a>
    </div>
    <div class="credit">Powered by <b>JAHID X EMPIRE</b> — Friend Request Service</div>
  </div>
</div></div>
""" + FX_SCRIPT + """
</body></html>
"""

PANEL_TEMPLATE = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JXE FRIEND REQ SPAM — Control Panel</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
""" + SHARED_STYLE + """
</head><body>
""" + WALLPAPER + """

""" + PRELOADER + LOADER_BOX + """
<div class="wrap"><div class="card-shell">
  <div class="brand">
    <div class="mark"></div>
    <div class="name">CONTROL PANEL</div>
  </div>
""" + HERO + """
  <h1 class="title" style="text-align:center">JXE <span class="accent">FRIEND REQ SPAM</span></h1>
  <div class="subtitle">
    <span class="dot"></span><span style="color:#4ade80">Service Online</span>
    <span style="opacity:.4">•</span>
    <span>{{ region_count }} regions available</span>
    <span style="opacity:.4">•</span>
    <span>{{ account_count }} accounts loaded</span>
  </div>

  <div class="section">
    <h3>Send Request</h3>
    <form method="get" action="/jxe/spam" id="spamForm" onsubmit="document.getElementById('loader').classList.add('on')">
      <div class="form-row">
        <div>
          <label class="field-label">Target UID</label>
          <input class="input" name="uid" placeholder="e.g. 123456789" required inputmode="numeric" pattern="[0-9]+">
        </div>
        <div>
          <button class="btn primary" type="submit" style="height:46px">Launch →</button>
        </div>
      </div>
      <input type="hidden" name="region" id="regionField" value="">
      <div class="hint" style="margin-top:12px;display:flex;align-items:center;gap:10px;flex-wrap:wrap">
        Selected region: <span class="selected-tag" id="selectedTag">All regions</span>
      </div>
    </form>
  </div>

  <div class="section">
    <h3>Available Regions · Click to Select</h3>
    <div style="display:flex;justify-content:flex-end;margin-bottom:10px">
      <button type="button" class="btn ghost" style="padding:6px 14px;font-size:.75rem" onclick="pickRegion('','All regions',this)">All regions</button>
    </div>
    <div class="region-grid">
      {% for code, label in regions %}
      <a href="javascript:void(0)" class="region-card" data-code="{{ code }}" onclick="pickRegion('{{ code }}','{{ label }}',this)" style="animation-delay:{{ loop.index0 * 0.05 }}s">
        <div class="flag"><img src="https://flagcdn.com/w80/{{ flag_iso.get(code, code) }}.png" alt="{{ code }}"></div>
        <div>
          <div class="label">{{ label }}</div>
          <div class="code">{{ code }}</div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>

  <script>
    function pickRegion(code,label,el){
      document.getElementById('regionField').value=code;
      document.getElementById('selectedTag').textContent=label;
      document.querySelectorAll('.region-card').forEach(c=>c.classList.remove('active'));
      if(el && el.classList.contains('region-card')) el.classList.add('active');
    }
  </script>

  <div class="section">
    <h3>Official Telegram Channel</h3>
    <a href="https://t.me/Jahid_x_Empire" target="_blank" style="display:flex;align-items:center;gap:16px;padding:16px 20px;border-radius:14px;background:linear-gradient(135deg,rgba(0,136,204,.18),rgba(0,180,255,.08));border:1px solid rgba(0,180,255,.3);text-decoration:none;transition:.3s" onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 12px 30px rgba(0,180,255,.25)'" onmouseout="this.style.transform='';this.style.boxShadow=''">
      <div style="width:52px;height:52px;border-radius:14px;background:linear-gradient(135deg,#0088cc,#00b4ff);display:grid;place-items:center;font-size:1.6rem;box-shadow:0 6px 20px rgba(0,180,255,.4);animation:pulse 2s ease-in-out infinite"><span style="display:block;width:18px;height:18px;border:2px solid #fff;border-radius:50%;border-top-color:transparent;animation:spin 1.4s linear infinite"></span></div>
      <div style="flex:1">
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;color:#f4f6fb;font-size:1.05rem">@Jahid_x_Empire</div>
        <div style="color:#8ea3c7;font-size:.85rem;margin-top:2px">Join for updates, new tools & premium access</div>
      </div>
      <div class="btn tg" style="pointer-events:none">Join Now →</div>
    </a>
  </div>

  <div class="section">
    <h3>REST API</h3>
    <div class="api-box"><b>GET</b> /api/spam?uid=<i>&lt;target_uid&gt;</i>&amp;region=<i>&lt;code|blank&gt;</i></div>
    <div class="hint">Returns JSON: <code>{success, failed, accounts_used, region_names, response_counts}</code>. Same engine, no HTML.</div>
    <div class="api-box" style="margin-top:10px"><b>GET</b> /health &nbsp;→&nbsp; <span style="color:#4ade80">{"status":"ok"}</span></div>
  </div>

  <div class="footer">
    <div class="btn-row">
      <a href="https://t.me/Jahid_x_Empire" target="_blank" class="btn tg"><span style="width:8px;height:8px;border-radius:50%;background:#fff;box-shadow:0 0 8px #fff;animation:pulse 1.6s ease-in-out infinite"></span>Join Channel</a>
      <a href="https://t.me/Itz_Jahid_X" target="_blank" class="btn primary">Contact Owner</a>
    </div>
    <div class="credit">Powered by <b>JAHID X EMPIRE</b> — Web Panel + JSON API</div>
  </div>
</div></div>
""" + FX_SCRIPT + """
</body></html>
"""

@app.route('/', methods=['GET'])
def CONTROL_PANEL():
    return render_template_string(
        PANEL_TEMPLATE,
        regions=[(c, REGION_LABEL.get(c, c.upper())) for c, _ in ALL_REGIONS],
        region_count=len(ALL_REGIONS),
        account_count=len(load_accounts()),
        flag_iso=FLAG_ISO,
    )

@app.route('/jxe/spam', methods=['GET'])
def START_SPAM():
    target_uid = request.args.get('uid')
    if not target_uid:
        return render_template_string("<h1 style='color:#f87171;font-family:sans-serif;padding:40px'>Error: Missing 'uid' parameter</h1>"), 400

    region_param = request.args.get('region')
    region = region_param.strip() if region_param else None

    result = spam_friend_requests(target_uid, region)
    if isinstance(result, tuple) and result[1] == 404:
        return render_template_string("<h1 style='color:#f87171;font-family:sans-serif;padding:40px'>Error: " + result[0]['error'] + "</h1>"), 404

    print("\n========== FINAL REPORT ==========")
    print(f"Total Accounts Used: {result.get('accounts_used', 0)}")
    print(f"Success: {result.get('success', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
    print("==================================\n")

    return render_template_string(
        HTML_TEMPLATE,
        target_uid=target_uid,
        data=result,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        flag_iso=FLAG_ISO,
        region_label=REGION_LABEL,
    )

@app.route('/api/spam', methods=['GET'])
def API_SPAM():
    target_uid = request.args.get('uid')
    if not target_uid:
        return jsonify({"error": "Missing 'uid' parameter"}), 400
    region_param = request.args.get('region')
    region = region_param.strip() if region_param else None
    result = spam_friend_requests(target_uid, region)
    if isinstance(result, tuple) and result[1] == 404:
        return jsonify(result[0]), 404
    return jsonify({
        "target_uid": target_uid,
        "region": region or "all",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **result,
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
