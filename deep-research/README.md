# ⚙️ Config Lab: Altyapı ve Sunucu Sıkılaştırma (Hardening) Kılavuzu
## 📌 Konu: PHP, Next.js, Docker, Nginx, cPanel ve VPS Katmanlarında Üretim Ortamı Güvenliği

---

## 🐘 1. PHP 8.4 Sunucu Çekirdek Güvenliği (`php.ini` Sıkılaştırması)

### 🛑 MODULE 01: Memory & Resource Limits (Bellek ve Kaynak Limitleri)
* **Açıklama:** Sunucunun kaynak tükenmesi (Resource Exhaustion) ve DoS saldırılarıyla çökmesini engeller.
```ini
memory_limit = 256M
max_execution_time = 30
max_input_time = 60

file_uploads = On
upload_max_filesize = 20M
post_max_size = 32M

opcache.enable = 1
opcache.memory_consumption = 128
opcache.interned_strings_buffer = 8
opcache.max_accelerated_files = 10000
opcache.validate_timestamps = 0

### 🔑 MODULE 05 & MODULE 06: Session Management & Session Security
* **Açıklama:** Çerez hırsızlığı (Session Hijacking) ve Bilgi Çalıcılara (InfoStealers) karşı çerez nitelikleri sıkılaştırılmıştır.
```ini
session.cookie_httponly = On
session.cookie_secure = On
session.cookie_samesite = "Strict"
session.use_strict_mode = On

open_basedir = "/var/www/html/:/tmp/"

display_errors = Off
display_startup_errors = Off
log_errors = On
error_log = /var/log/php/error.log
expose_php = Off
disable_functions = exec, passthru, shell_exec, system, proc_open, popen, eval, assert

server_tokens off; # Bilgi sızıntısını önler

# Gelişmiş Güvenlik Başlıkları (Security Headers)
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# TLS Sıkılaştırma ve DoS Savunması
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
client_max_body_size 2m;
limit_req_zone $binary_remote_addr zone=ddos_defense:10m rate=5r/s;

---

## 🐋 3. Sertleştirilmiş Dockerfile Yapısı (Next.js & Coolify)

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

USER node # Root dışı güvenli kullanıcı çalıştırma ortamı
EXPOSE 3000
CMD ["npm", "start"]

Port 2222                 # Standart port değiştirildi
PermitRootLogin no        # Doğrudan root erişimi kapatıldı
PasswordAuthentication no # Sadece SSH Key zorunlu kılındı
MaxAuthTries 3            # Hatalı deneme sınırı

net.ipv4.tcp_syncookies = 1           # SYN Flood (DoS) engelleme
net.ipv4.conf.all.rp_filter = 1       # IP Spoofing koruması
net.ipv4.conf.all.accept_redirects = 0 # ICMP Kapatma
