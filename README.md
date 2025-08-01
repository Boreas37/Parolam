# Parolam Project

Bu proje, Have I Been Pwned (HIBP) hizmetine benzer şekilde çalışmak üzere tasarlanmış, on-premise olarak kullanılabilen bir veri ihlali sorgulama sistemidir. Arka planda yüksek performanslı sorgulama için ClickHouse veritabanı kullanılmaktadır.

## Docker ile kurulum:

### 1. Projeyi İndirin
```bash
git clone https://github.com/Boreas37/parolam.git
cd parolam
```

### 2. Environment Variables Ayarlayın
```bash
# env.example dosyasını .env olarak kopyalayın
cp env.example .env

# .env dosyasını düzenleyin
nano .env
```

`.env` dosyasını şu şekilde düzenleyin:
```env
# ClickHouse Database Configuration
CH_HOST=clickhouse
CH_PORT=8123
CH_USER=default
CH_PASSWORD=your_secure_password
CH_DATABASE=parolam

# Flask Application Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=80
FLASK_DEBUG=False

# Import Configuration
DEFAULT_BREACH_NAME=
DEFAULT_BREACH_DATE=
BATCH_SIZE=100000
```

### 3. Docker Compose ile Çalıştırın
```bash
# Sistemi başlatın
docker-compose up -d

# Sistemi durdurun
docker-compose down
```

### 4. Veritabanı Kurulumu
```bash
# Veritabanı tablolarını oluşturun
python db_create.py
```

### 5. Veri İçe Aktarma
```bash
# Verileri içe aktarın
python db_import.py --input veri(Opsiyonel; --batch number, .env dosyasında default 100000 tanımlı.)
```

### 6. Web Uygulamasına Erişim
Tarayıcınızda `http://localhost` adresine gidin.

## 🔧 Manuel Kurulum

### 1. Environment Variables Kurulumu
```bash
cp env.example .env
# .env dosyasını düzenleyin
```

### 2. Python Dependencies Kurulumu
```bash
pip install -r requirements.txt
```

### 3. ClickHouse Kurulumu
```bash
# Ubuntu/Debian
sudo apt-get install clickhouse-server clickhouse-client

# macOS
brew install clickhouse

# Windows
# https://clickhouse.com/docs/en/install#install-from-deb-packages
```

### 4. Veritabanı Kurulumu
```bash
python db_create.py
```

### 5. Veri İçe Aktarma
```bash
python db_import.py --input veri
```

### 6. Web Uygulamasını Çalıştırma
```bash
cd web
python app.py
```

## 🐳 Docker Komutları

### Temel Komutlar
```bash
# Sistemi başlat
docker-compose up -d

# Sistemi durdur
docker-compose down

# Servisleri yeniden başlat
docker-compose restart

# Tüm verileri sil
docker-compose down -v
```

### Geliştirme Komutları
```bash
# Web servisini yeniden build et
docker-compose build web

# Sadece web servisini yeniden başlat
docker-compose restart web

# ClickHouse'a bağlan
docker-compose exec clickhouse clickhouse-client

# Web container'ına bağlan
docker-compose exec web bash
```

### Veri İşlemleri
```bash
# Veritabanı tablolarını oluştur
python db_create.py

# Veri içe aktar
python db_import.py --input veri

# Backup al
docker-compose exec clickhouse clickhouse-client --query "BACKUP TABLE parolam.* TO '/backup'"
```

##  Environment Variables Açıklaması

### ClickHouse Ayarları
- `CH_HOST`: ClickHouse sunucu adresi (Docker'da: `clickhouse`)
- `CH_PORT`: ClickHouse port numarası (varsayılan: `8123`)
- `CH_USER`: ClickHouse kullanıcı adı (varsayılan: `default`)
- `CH_PASSWORD`: ClickHouse şifresi (**zorunlu**)
- `CH_DATABASE`: Veritabanı adı (varsayılan: `parolam`)

### Flask Ayarları
- `FLASK_HOST`: Flask uygulamasının host'u (varsayılan: `0.0.0.0`)
- `FLASK_PORT`: Flask uygulamasının port'u (varsayılan: `80`)
- `FLASK_DEBUG`: Debug modu (production'da `False`)

### İçe Aktarma Ayarları
- `DEFAULT_BREACH_NAME`: Varsayılan sızıntı adı
- `DEFAULT_BREACH_DATE`: Varsayılan sızıntı tarihi
- `BATCH_SIZE`: Toplu işlem boyutu (varsayılan: `100000`)

##  Proje Yapısı

```
parolam/
├── web/                   # Web uygulaması
│   ├── app.py             # Flask uygulaması
│   ├── Dockerfile         # Web container
│   └── templates/         # HTML şablonları
├── veri/                  # Veri dosyaları
├── db_create.py           # Veritabanı oluşturma
├── db_import.py           # Veri içe aktarma
├── docker-compose.yml     # Docker compose
├── requirements.txt       # Python dependencies
├── env.example            # Environment template
└── README.md              # Bu dosya
```

## Yapılacaklar

### Öncelikli Özellikler

#### 1. **Gelişmiş API Sistemi**
- [ ] API endpoint'leri oluşturma
- [ ] API rate limiting ve authentication
- [ ] Gerçek bir API dökümantasyonu

#### 2. **Otomatik Şifre Kontrol Mekanizması**
- [ ] Tek dosyalık JavaScript kütüphanesi
- [ ] Kayıt formlarına otomatik entegrasyon
- [ ] Şifre gücü göstergesi

#### 3. **Monitoring ve Analytics**
- [ ] Application performance monitoring
- [ ] Health check endpoint'leri


