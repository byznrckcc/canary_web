import base64
import os
import logging
from logging.handlers import RotatingFileHandler
import uuid
import hashlib
import time
import queue
import threading
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string, render_template
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from canary_web.models.forensics import Base, CanaryHit, ThreatLevel

# ── 1. MERKEZİ STRATEJİK YAPILANDIRMA (TACTICAL CONFIGURATION) ───────────────
class CyberCommandConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ultra_secure_deception_mesh_cipher_2026")
    DATABASE_URI = "sqlite:///canary_dev.db"
    DEBUG = True
    PORT = 5000
    HOST = "0.0.0.0"
    SYSTEM_BANNER = "Tactical-Deception-Mesh/v2.4.0-Enterprise"

app = Flask(__name__)
app.config.from_object(CyberCommandConfig)

# ── 2. ENDÜSTRİYEL LOGLAMA VE GÜNLÜKLEME SİSTEMİ ─────────────────────────────
log_handler = RotatingFileHandler('canary_mesh_system.log', maxBytes=5000000, backupCount=10)
log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [SUBSYSTEM::%(name)s] %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger("TacticalCore")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Veritabanı Dişli Entegrasyonu
engine = create_engine(app.config["DATABASE_URI"], echo=False)
SessionLocal = sessionmaker(bind=engine)

# ── 3. ASENKRON ADLİ BİLİŞİM LOG KUYRUĞU (HIGH-PERFORMANCE ASYNC QUEUE) ──────
# Sistem performansını maksimuma çıkarmak ve darboğazı engellemek için arka plan thread'i
log_queue = queue.Queue()

def async_log_worker():
    """Arka planda sessizce çalışan, kuyruğa düşen adli logları DB'ye işleyen motor."""
    while True:
        hit_data = log_queue.get()
        if hit_data is None:
            break
        
        db = SessionLocal()
        try:
            hit = CanaryHit(
                token_id=hit_data['token_id'],
                ip_address=hit_data['ip_address'],
                user_agent=hit_data['user_agent'],
                referer=hit_data['referer'],
                http_method=hit_data['http_method'],
                screen_resolution=hit_data.get('screen_resolution'),
                system_languages=hit_data.get('system_languages'),
                threat_level=hit_data['threat_level'],
                notes=hit_data.get('notes'),
                country=hit_data.get('country'),
                asn=hit_data.get('asn')
            )
            hit.populate_datacenter_flag()
            if hit.is_vpn_or_tor:
                hit.threat_level = ThreatLevel.CRITICAL
            hit.set_fingerprint(extra=hit_data.get('screen_resolution', ''))
            
            db.add(hit)
            db.commit()
            logger.info(f"💾 Asenkron Adli Kayıt DB'ye İşlendi: Token={hit.token_id} IP={hit.ip_address}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Kuyruk İşleme Hatası: {str(e)}")
        finally:
            db.close()
            log_queue.task_done()

# Arka plan işçisini (Worker Thread) ateşliyoruz
worker_thread = threading.Thread(target=async_log_worker, daemon=True)
worker_thread.start()

# ── 4. KRİPTOGRAFİK ALDATMACA ENCODERI (DECEPTION TOKEN OBFUSCATOR) ──────────
class DeceptionTokenObfuscator:
    """Tokenları rastgele göstermeyip, siber saldırganların iştahını kabartacak kurumsal hash kalıplarına sokar."""
    @staticmethod
    def encode_to_vault_key(raw_id):
        salt = "X-CYBER-MESH-"
        hashed = hashlib.sha256((raw_id + salt).encode()).hexdigest()[:16]
        return f"AKIAIOSFODNN7_{hashed.upper()}"

    @staticmethod
    def encode_to_jwt(raw_id):
        header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().strip("=")
        payload = base64.b64encode(f'{{"user":"root","scope":"adm","tid":"{raw_id[:8]}"}}'.encode()).decode().strip("=")
        signature = hashlib.sha256(f"{header}.{payload}".encode()).hexdigest()[:24]
        return f"{header}.{payload}.{signature}"

# ── 5. LOKAL TEHDİT İSTİHBARATI VE COĞRAFİ SİMÜLATÖR (LOCAL THREAT INTEL) ────
def analyze_ip_intelligence(ip_address):
    """Gelen IP adresini simüle edilmiş tehdit istihbarat ağından geçirir."""
    if ip_address == "127.0.0.1":
        return {"country": "TR", "asn": "AS15897 (Turk Telekom)", "status": "LOCAL_SIM"}
    
    # Simüle edilmiş siber istihbarat veri tabanı
    hash_ip = int(hashlib.md5(ip_address.encode()).hexdigest(), 16)
    if hash_ip % 3 == 0:
        return {"country": "US", "asn": "AS16509 (Amazon.com DB Node)", "status": "DATACENTER"}
    elif hash_ip % 3 == 1:
        return {"country": "RU", "asn": "AS43317 (Tor Exit Relay)", "status": "TOR_NODE"}
    else:
        return {"country": "NL", "asn": "AS14340 (Leaseweb B.V.)", "status": "SUSPICIOUS"}

def generate_tactical_firewall_rules(ip_address):
    """Saldırgan yakalandığı an jüriye gösterilecek canlı engelleme komutları."""
    return {
        "iptables": f"sudo iptables -A INPUT -s {ip_address} -j DROP -m comment --comment 'CANARY-WEB MESH DETECTED'",
        "snort": f"drop tcp {ip_address} any -> $INTERNAL_NET any (msg:'CANARY-WEB DETECTED INTENTIONAL ATTACK'; sid:999001;)",
        "pfsense_api": f"curl -X POST https://pfsense.isu.edu/api/v1/block -d 'ip={ip_address}&scope=global'"
    }

# ── 6. GLOBAL CONTEXT VE MIDDLEWARE KATMANLARI ──────────────────────────────
@app.after_request
def inject_enterprise_security_headers(response):
    """OWASP Standartlarında sıkılaştırılmış HTTP Güvenlik Başlıkları."""
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self' https://cdn.jsdelivr.net;"
    response.headers["Server"] = CyberCommandConfig.SYSTEM_BANNER
    return response

@app.context_processor
def inject_system_time():
    return {'now': datetime.now(timezone.utc)}

# ── 7. PLATFORM ROTASI: SİBER KOMUTA MERKEZİ (TACTICAL SOC DASHBOARD) ────────
@app.route("/dashboard", methods=["GET"])
def dashboard_view():
    db = SessionLocal()
    try:
        all_hits = db.query(CanaryHit).order_by(CanaryHit.created_at.desc()).all()
        total_hits = len(all_hits)
        critical_hits = db.query(CanaryHit).filter(CanaryHit.threat_level == ThreatLevel.CRITICAL).count()
        unique_tokens = db.query(func.count(CanaryHit.token_id.distinct())).scalar() or 0
        
        # Her adli bilişim loguna dinamik firewall kuralları bağlama
        for hit in all_hits:
            hit.generated_rules = generate_tactical_firewall_rules(hit.ip_address or "127.0.0.1")
            
        return render_template(
            "dashboard.html", 
            hits=all_hits, total_hits=total_hits, 
            critical_hits=critical_hits, unique_tokens=unique_tokens
        )
    except Exception as e:
        logger.error(f"Dashboard DB Sorgu Hatası: {str(e)}")
        return f"System Mesh Critical Failure: {str(e)}", 500
    finally:
        db.close()

# ── 8. PLATFORM ROTASI: ÇOKLU TUZAK GENERATORÜ (DECEPTION MATRIX GENERATOR) ──
@app.route("/api/v1/tokens/generate", methods=["POST"])
def generate_token():
    raw_uuid = str(uuid.uuid4())
    
    # Saldırganın aklını başından alacak maskelenmiş tuzaklar üretiliyor
    vault_key = DeceptionTokenObfuscator.encode_to_vault_key(raw_uuid)
    jwt_token = DeceptionTokenObfuscator.encode_to_jwt(raw_uuid)
    
    logger.info(f"🛠️ Yeni Siber Aldatmaca Matrisi Oluşturuldu. Dahili ID: {raw_uuid}")
    
    return jsonify({
        "status": "COMPLETED",
        "internal_reference_id": raw_uuid,
        "deception_matrix_deployments": {
            "web_beacon_invisible_endpoint": f"{request.url_root}t/{raw_uuid}",
            "wordpress_admin_bruteforce_trap": f"{request.url_root}wp-admin/auth/{raw_uuid[:8]}",
            "cloud_vault_credentials_leak": f"{request.url_root}api/v2/vault/keys/{vault_key}"
        },
        "obfuscated_artifacts": {
            "sahte_aws_key": vault_key,
            "sahte_session_jwt": jwt_token
        }
    }), 201

# ── 9. MİKRO TUZAK ROTASI 1: WORDPRESS PANEL TUZAĞI (`/wp-admin`) ────────────
@app.route("/wp-admin/auth/<short_id>", methods=["GET", "POST"])
def wordpress_trap(short_id):
    intel = analyze_ip_intelligence(request.remote_addr)
    
    # Log verisini asenkron kuyruğa gönderiyoruz (Sistem hiç bekleme yapmıyor!)
    log_queue.put({
        "token_id": f"wp_brute_{short_id}", "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"), "referer": request.headers.get("Referer"),
        "http_method": request.method, "threat_level": ThreatLevel.HIGH,
        "notes": "CMS Zafiyet Taraması: Saldırgan sahte WordPress admin paneline kaba kuvvet denemesi yaptı.",
        "country": intel["country"], "asn": intel["asn"]
    })
    
    return "<strong>Fatal error:</strong> Call to undefined function wp_signon() in /var/www/html/wp-includes/user.php on line 43", 500

# ── 10. MİKRO TUZAK ROTASI 2: BULUT VERİ KASASI API TUZAĞI (`/api/v2/vault`) ─
@app.route("/api/v2/vault/keys/<vault_key>", methods=["GET", "POST"])
def cloud_vault_trap(vault_key):
    intel = analyze_ip_intelligence(request.remote_addr)
    
    log_queue.put({
        "token_id": f"vault_leak_{vault_key[:12]}", "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"), "referer": request.headers.get("Referer"),
        "http_method": request.method, "threat_level": ThreatLevel.HIGH,
        "notes": "Credential Stuffing: Saldırgan sızdırılmış sahte bulut anahtarını API üzerinden test etmeye çalıştı.",
        "country": intel["country"], "asn": intel["asn"]
    })
    
    return jsonify({"error": "Resource locked", "code": "ERR_VAULT_INTEGRITY_VIOLATION", "status": "Unauthorized"}), 401

# ── 11. MİKRO TUZAK ROTASI 3: STANDART WEB BEACON BAĞLANTISI (TRIGGER) ───────
@app.route("/t/<uuid_id>", methods=["GET"])
def trigger_point(uuid_id):
    telemetry_js_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script>
            window.onload = function() {
                var clientData = {
                    token_id: "{{ token_id }}",
                    screen_resolution: window.screen.width + "x" + window.screen.height,
                    system_languages: navigator.languages ? navigator.languages.join(",") : navigator.language
                };
                fetch("/api/v1/telemetry/capture", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(clientData)
                }).then(function() {
                    window.location.href = "/error-page?event=" + "{{ token_id }}";
                }).catch(function() {
                    window.location.href = "/error-page?event=" + "{{ token_id }}";
                });
            };
        </script>
    </head>
    <body style="background-color: #020408;"></body>
    </html>
    """
    user_agent = request.headers.get("User-Agent", "").lower()
    
    # Otomatize araçları anında filtreleme hattı
    if any(bot in user_agent for bot in ["curl", "wget", "python", "nikto", "nmap", "sqlmap", "dirb"]):
        intel = analyze_ip_intelligence(request.remote_addr)
        log_queue.put({
            "token_id": uuid_id, "ip_address": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"), "referer": request.headers.get("Referer"),
            "http_method": request.method, "threat_level": ThreatLevel.HIGH,
            "notes": f"Otomatize Siber Tarama/Keşif Robotu Bloklandı: {user_agent}",
            "country": intel["country"], "asn": intel["asn"]
        })
        return jsonify({"status": "Access Denied", "code": "SIG_RECON_DETECTED"}), 403

    return render_template_string(telemetry_js_template, token_id=uuid_id)

# ── 12. TELEMETRİ ALICI BORU HATTI (PIPELINE CAPTURE) ────────────────────────
@app.route("/api/v1/telemetry/capture", methods=["POST"])
def telemetry_capture():
    data = request.get_json() or {}
    token_id = data.get("token_id")
    if not token_id: 
        return jsonify({"status": "malformed_payload"}), 400
    
    intel = analyze_ip_intelligence(request.remote_addr)
    
    # Veriler anlık kuyruğa fırlatılıyor
    log_queue.put({
        "token_id": token_id,
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
        "http_method": "GET",
        "screen_resolution": data.get("screen_resolution"),
        "system_languages": data.get("system_languages"),
        "threat_level": ThreatLevel.HIGH,
        "notes": "Tarayıcı (Browser) üzerinden derin telemetri ve adli parmak izi toplandı.",
        "country": intel["country"],
        "asn": intel["asn"]
    })
    
    return jsonify({"status": "telemetry_queued"}), 200

@app.route("/error-page")
def error_page():
    return "<h1>404 Not Found</h1>The requested URL was not found on this server.", 404

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    logger.info("🔥 Deception Tactical Mesh Enterprise Engine fully armed.")
    print("[+] 🔒 SİBER KOMUTA MERKEZİ: DEVASA KURUMSAL ARKA PLAN MOTORU AKTİF!")
    app.run(host=CyberCommandConfig.HOST, port=CyberCommandConfig.PORT, debug=CyberCommandConfig.DEBUG)
