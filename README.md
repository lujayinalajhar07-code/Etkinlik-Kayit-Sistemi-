# 🎫 Etkinlik Kayıt Sistemi (Ultra-Modern GUI)

Bu proje, etkinlik yönetimi, katılımcı takibi ve biletleme işlemlerini gerçekleştirmek için tasarlanmış, fütüristik bir kullanıcı arayüzüne (GUI) sahip Python uygulamasıdır. Glassmorphism tasarımı ve koyu tema estetiği ile modern yazılım standartlarını sunar.

## ✨ Öne Çıkan Özellikler

- **Ultra-Modern Arayüz:** PyQt5 ile geliştirilmiş, animasyonlu arka plan ve cam efekti (glassmorphism) içeren şık tasarım.
- **Dinamik Dashboard:** Toplam gelir, aktif etkinlikler ve katılımcı sayılarını anlık olarak gösteren istatistik paneli.
- **Etkinlik Yönetimi:** Kapasite kontrolü, bilet fiyatlandırması ve konum bilgileriyle yeni etkinlikler oluşturma.
- **Gelişmiş Biletleme:** Standart, VIP, Öğrenci ve Grup bilet türleri için otomatik fiyat çarpanları ve bilet iptal sistemi.
- **Detaylı Raporlama:** Etkinlik doluluk oranları ve bilet türü dağılımını görsel barlar ile raporlama.
- **Bildirim Sistemi:** Kullanıcı işlemlerine anlık geri bildirim veren (toast) bildirimler.

## 🚀 Kurulum

### Gereksinimler
Uygulamayı çalıştırmak için bilgisayarınızda Python 3 ve `PyQt5` kütüphanesinin yüklü olması gerekir:

```bash
pip install PyQt5
```

## 🛠️ Kullanım

Uygulamayı başlatmak için ana dizinde şu komutu çalıştırın:

```bash
python "etkinlik (3).txt"
```
*(Not: Kod dosyanızın adı farklıysa komutu ona göre düzenleyin.)*

## 📁 Proje Yapısı

- **`EtkinlikSistemi` (Backend):** İş mantığını, bilet hesaplamalarını ve veri yönetimini sağlayan çekirdek sınıflar.
- **`MainWindow` (Frontend):** Navigasyon rayı, sayfa yönetimi ve ana uygulama döngüsü.
- **Sayfalar:** 
  - **Genel (Dashboard):** Sistemin genel özeti.
  - **Etkinlikler:** Etkinlik ekleme ve silme.
  - **Üyeler:** Katılımcı kayıt ve yönetimi.
  - **Biletler:** Satış ve iptal işlemleri.
  - **Raporlar:** Veri analizi ve görsel sunum.

## 🎨 Tasarım Detayları

- **Renk Paleti:** Deep Space Blue, Cyan Glow, Emerald Green ve Rose Red.
- **Font:** Segoe UI / DemiBold.
- **Efektler:** QGraphicsDropShadow, QPropertyAnimation ve Radial Gradients.

---
*Bu proje, Python ve PyQt5 gücünü birleştirerek estetik ve fonksiyonelliği bir araya getirmektedir.*
