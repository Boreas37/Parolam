import hashlib
import time
import threading
import os
from dotenv import load_dotenv

import clickhouse_connect
from flask import Flask, jsonify, render_template, request, Response

load_dotenv()

app = Flask(__name__)

CH_HOST = os.getenv('CH_HOST')
CH_PORT = int(os.getenv('CH_PORT', 8123))
CH_USER = os.getenv('CH_USER')
CH_PASSWORD = os.getenv('CH_PASSWORD')
CH_DATABASE = os.getenv('CH_DATABASE', 'parolam')

if not CH_HOST:
    raise ValueError("CH_HOST environment variable is required")
if not CH_USER:
    raise ValueError("CH_USER environment variable is required")
if not CH_PASSWORD:
    raise ValueError("CH_PASSWORD environment variable is required")

_local = threading.local()

def get_db_client():
    
    if not hasattr(_local, 'client'):
        try:
            _local.client = clickhouse_connect.get_client(
                host=CH_HOST, port=CH_PORT, user=CH_USER, password=CH_PASSWORD, database=CH_DATABASE
            )
            _local.client.ping()
        except Exception as e:
            print(f"Veritabanı bağlantı hatası: {e}")
            _local.client = None
    
    return _local.client

def split_hash(hex_hash: str) -> tuple[str, str]:
    """40 karakterlik bir SHA1 hash'ini 6'lık prefix ve 34'lük suffix'e ayırır."""
    return hex_hash[:6], hex_hash[6:]


@app.route('/')
def index():
    return render_template('password.html')

@app.route('/email')
def email_page():
    return render_template('email.html')

@app.route('/password')
def password_page():
    return render_template('password.html')

@app.route('/api')
def api_page():
    return render_template('api.html')



@app.route('/api/stats')
def get_stats():
    """Veritabanı istatistiklerini döndürür."""
    client = get_db_client()
    if not client:
        return jsonify({"error": "Veritabanı bağlantı hatası."}), 500

    try:
        email_count_result = client.query("SELECT count() FROM email_leaks")
        email_count = email_count_result.result_rows[0][0]
        
        password_count_result = client.query("SELECT count() FROM password_leaks")
        password_count = password_count_result.result_rows[0][0]
        
        breach_count_result = client.query("SELECT count() FROM breach_metadata")
        breach_count = breach_count_result.result_rows[0][0]
        
        return jsonify({
            "email_count": email_count,
            "password_count": password_count,
            "breach_count": breach_count
        })
    except Exception as e:
        return jsonify({"error": f"İstatistik hesaplama hatası: {e}"}), 500

@app.route('/check-email', methods=['POST'])
def check_email():
    email = request.json.get('email')
    if not email:
        return jsonify({"error": "E-posta adresi gerekli."}), 400

    client = get_db_client()
    if not client:
        return jsonify({"error": "Veritabanı bağlantı hatası."}), 500

    email_hash = hashlib.sha1(email.encode('utf-8')).hexdigest().upper()
    email_prefix, email_suffix = split_hash(email_hash)
    
    query_params = {'prefix': email_prefix, 'suffix': email_suffix}
    breach_ids_result = client.query(
        "SELECT breach_id FROM email_leaks WHERE email_prefix = %(prefix)s AND email_suffix = %(suffix)s",
        parameters=query_params
    )
    
    if not breach_ids_result.result_rows:
        return jsonify({"pwned": False})

    breach_ids = [row[0] for row in breach_ids_result.result_rows]
    metadata_result = client.query(
        "SELECT breach_name, breach_date FROM breach_metadata WHERE breach_id IN %(ids)s",
        parameters={'ids': breach_ids}
    )
    
    breaches = [
        {"name": row[0], "date": row[1].strftime('%d-%m-%Y')} for row in metadata_result.result_rows
    ]
    
    return jsonify({"pwned": True, "breaches": breaches})


@app.route('/check-password/<string:prefix>')
def check_password(prefix: str):
    prefix = prefix.upper()
    if not (len(prefix) == 6 and all(c in '0123456789ABCDEF' for c in prefix)):
        return Response("Geçersiz prefix.", status=400, mimetype="text/plain")

    client = get_db_client()
    if not client:
        return Response("Veritabanı bağlantı hatası.", status=500, mimetype="text/plain")
        
    result = client.query(
        "SELECT hash_suffix, sum(prevalence) as total_count FROM password_leaks WHERE hash_prefix = %(prefix)s GROUP BY hash_suffix",
        parameters={'prefix': prefix}
    )

    # Bytes string'leri normal string'e çevir
    response_lines = []
    for row in result.result_rows:
        suffix = row[0].decode('utf-8') if isinstance(row[0], bytes) else str(row[0])
        count = row[1]
        response_lines.append(f"{suffix}:{count}")
    
    response_text = "\r\n".join(response_lines)
    return Response(response_text, mimetype="text/plain")


if __name__ == '__main__':
    flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
    flask_port = int(os.getenv('FLASK_PORT', 80))
    flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=flask_host, port=flask_port, debug=flask_debug)