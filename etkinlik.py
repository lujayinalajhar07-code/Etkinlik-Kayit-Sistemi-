"""
╔══════════════════════════════════════════════════════════════╗
║       🎫 Etkinlik Kayıt Sistemi — Event Registration System  ║
║       OOP prensipleri ile geliştirilmiş, modüler yapı        ║
║       Sınıflar: Etkinlik | Katilimci | Bilet                 ║
╚══════════════════════════════════════════════════════════════╝

Araç Paylaşım Sistemi mimarisi baz alınarak dönüştürülmüştür.
Arac        → Etkinlik    (etkinlik bilgisi ve kapasitesi)
Kullanici   → Katilimci   (katılımcı bilgisi ve bilet geçmişi)
Kiralama    → Bilet       (kayıt işlemi ve doğrulama)
Odeme       → (Bilet içinde entegre)
Rapor       → Rapor       (katılım ve gelir raporları)
PaylasimSistemi → EtkinlikSistemi (merkezi yönetici)
"""

from enum import Enum
from datetime import datetime, date
from typing import Optional
import json
import os


# ==================== ENUMS ====================

class BiletTuru(Enum):
    """Bilet türlerini standart ve kontrollü şekilde tutar"""
    STANDART   = "Standart"
    VIP        = "VIP"
    OGRENCI    = "Öğrenci"
    GRUP       = "Grup (5+ kişi)"


# ==================== MODEL SINIFLAR ====================

class Etkinlik:
    """
    Etkinlik bilgilerini ve kapasite durumunu yöneten sınıf.
    (Arac sınıfının karşılığı)

    Özellikler:
        etkinlik_id  : Benzersiz etkinlik kimliği
        ad           : Etkinlik adı
        tarih        : Etkinlik tarihi (datetime)
        konum        : Etkinliğin yapılacağı yer
        kapasite     : Maksimum katılımcı sayısı
        bilet_fiyati : Standart bilet ücreti
        aktif_mi     : Kayıt açık/kapalı durumu
    """

    def __init__(self, etkinlik_id: str, ad: str, tarih: datetime,
                 konum: str, kapasite: int, bilet_fiyati: float):
        self._etkinlik_id  = etkinlik_id
        self._ad           = ad
        self._tarih        = tarih
        self._konum        = konum
        self._kapasite     = kapasite
        self._bilet_fiyati = bilet_fiyati
        self._aktif_mi     = True          # Kayıt varsayılan olarak açık
        self._katilimci_sayisi = 0         # Şimdiye kadar alınan bilet adedi

    # === Getter Metotları ===
    def get_etkinlik_id(self) -> str:      return self._etkinlik_id
    def get_ad(self) -> str:               return self._ad
    def get_tarih(self) -> datetime:       return self._tarih
    def get_konum(self) -> str:            return self._konum
    def get_kapasite(self) -> int:         return self._kapasite
    def get_bilet_fiyati(self) -> float:   return self._bilet_fiyati
    def get_aktif_mi(self) -> bool:        return self._aktif_mi
    def get_katilimci_sayisi(self) -> int: return self._katilimci_sayisi
    def get_bos_koltuk(self) -> int:       return self._kapasite - self._katilimci_sayisi

    # === İş Mantığı Metotları ===
    def kayit_durumu_guncelle(self, aktif: bool) -> None:
        """Etkinlik kayıt durumunu açar veya kapatır (Arac.arac_durumu_guncelle karşılığı)"""
        self._aktif_mi = aktif

    def katilimci_ekle(self) -> tuple[bool, str]:
        """
        Etkinliğe bir katılımcı ekler, kapasite kontrolü yapar.
        (Arac.kilometre_guncelle mantığından ilham alınmıştır)
        """
        if not self._aktif_mi:
            return False, f"'{self._ad}' etkinliği için kayıt kapalı."
        if self._katilimci_sayisi >= self._kapasite:
            return False, f"'{self._ad}' etkinliği doldu! Kapasite: {self._kapasite}"
        self._katilimci_sayisi += 1
        return True, "Katılımcı başarıyla eklendi."

    def katilimci_cikar(self) -> None:
        """Bilet iptalinde katılımcı sayısını azaltır"""
        if self._katilimci_sayisi > 0:
            self._katilimci_sayisi -= 1

    def doluluk_orani(self) -> float:
        """Etkinlik doluluk yüzdesini döndürür"""
        if self._kapasite == 0:
            return 0.0
        return (self._katilimci_sayisi / self._kapasite) * 100

    def to_dict(self) -> dict:
        return {
            "etkinlik_id":      self._etkinlik_id,
            "ad":               self._ad,
            "tarih":            self._tarih.isoformat(),
            "konum":            self._konum,
            "kapasite":         self._kapasite,
            "bilet_fiyati":     self._bilet_fiyati,
            "aktif_mi":         self._aktif_mi,
            "katilimci_sayisi": self._katilimci_sayisi
        }

    @classmethod
    def from_dict(cls, data: dict):
        e = cls(
            data["etkinlik_id"],
            data["ad"],
            datetime.fromisoformat(data["tarih"]),
            data["konum"],
            data["kapasite"],
            data["bilet_fiyati"]
        )
        e._aktif_mi         = data.get("aktif_mi", True)
        e._katilimci_sayisi = data.get("katilimci_sayisi", 0)
        return e

    def __repr__(self) -> str:
        durum = "✅ Açık" if self._aktif_mi else "🔒 Kapalı"
        return f"Etkinlik({self._etkinlik_id}, {self._ad}, {durum})"


# ─────────────────────────────────────────────────────────────

class Katilimci:
    """
    Katılımcı bilgilerini ve bilet geçmişini yöneten sınıf.
    (Kullanici sınıfının karşılığı)

    Özellikler:
        katilimci_id : Benzersiz katılımcı kimliği
        ad           : Ad soyad
        email        : E-posta adresi
        telefon      : Telefon numarası
        _biletler    : Katılımcının bilet listesi
    """

    def __init__(self, katilimci_id: str, ad: str, email: str, telefon: str = ""):
        self._katilimci_id = katilimci_id
        self._ad           = ad
        self._email        = email
        self._telefon      = telefon
        self._biletler     = []          # Katılımcıya ait tüm biletler

    # === Getter Metotları ===
    def get_katilimci_id(self) -> str: return self._katilimci_id
    def get_ad(self) -> str:           return self._ad
    def get_email(self) -> str:        return self._email
    def get_telefon(self) -> str:      return self._telefon

    # === İş Mantığı Metotları ===
    def bilet_ekle(self, bilet) -> None:
        """Katılımcının bilet listesine yeni bilet ekler (kiralama_ekle karşılığı)"""
        self._biletler.append(bilet)

    def bilet_gecmisi(self) -> list:
        """Katılımcının tüm bilet geçmişini döndürür"""
        return list(self._biletler)

    def aktif_bilet(self, etkinlik_id: str = None):
        """
        Katılımcının aktif (iptal edilmemiş) biletini döndürür.
        etkinlik_id verilirse o etkinliğe ait bileti arar.
        (aktif_kiralama karşılığı)
        """
        for b in self._biletler:
            if b.get_iptal_mi():
                continue
            if etkinlik_id is None or b.get_etkinlik().get_etkinlik_id() == etkinlik_id:
                return b
        return None

    def to_dict(self) -> dict:
        return {
            "katilimci_id": self._katilimci_id,
            "ad":           self._ad,
            "email":        self._email,
            "telefon":      self._telefon
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data["katilimci_id"],
            data["ad"],
            data["email"],
            data.get("telefon", "")
        )

    def __repr__(self) -> str:
        return f"Katilimci({self._katilimci_id}, {self._ad})"


# ─────────────────────────────────────────────────────────────

class Bilet:
    """
    Bilet oluşturma, doğrulama ve iptal işlemlerini yöneten sınıf.
    (Kiralama + Odeme sınıflarının birleşik karşılığı)

    Özellikler:
        bilet_id      : Benzersiz bilet kimliği
        etkinlik      : İlgili Etkinlik nesnesi
        katilimci     : İlgili Katilimci nesnesi
        bilet_turu    : Bilet türü (BiletTuru enum)
        kayit_tarihi  : Bilet oluşturulma zamanı
        ucret         : Ödenen ücret
        iptal_mi      : İptal durumu
    """

    # Bilet türüne göre fiyat çarpanı
    TUR_CARPAN = {
        BiletTuru.STANDART: 1.0,
        BiletTuru.VIP:      2.5,
        BiletTuru.OGRENCI:  0.5,
        BiletTuru.GRUP:     0.8,
    }

    def __init__(self, bilet_id: int, etkinlik: Etkinlik,
                 katilimci: Katilimci, bilet_turu: BiletTuru = BiletTuru.STANDART):
        self._bilet_id     = bilet_id
        self._etkinlik     = etkinlik
        self._katilimci    = katilimci
        self._bilet_turu   = bilet_turu
        self._kayit_tarihi = datetime.now()
        self._ucret        = 0.0
        self._iptal_mi     = False
        self._iptal_tarihi: Optional[datetime] = None

    # === Getter Metotları ===
    def get_bilet_id(self) -> int:        return self._bilet_id
    def get_etkinlik(self) -> Etkinlik:   return self._etkinlik
    def get_katilimci(self) -> Katilimci: return self._katilimci
    def get_bilet_turu(self) -> BiletTuru:return self._bilet_turu
    def get_kayit_tarihi(self) -> datetime:return self._kayit_tarihi
    def get_ucret(self) -> float:         return self._ucret
    def get_iptal_mi(self) -> bool:       return self._iptal_mi

    # === İş Mantığı Metotları ===
    def bilet_olustur(self) -> tuple[bool, str]:
        """
        Bilet oluşturur: etkinlik kapasitesini kontrol eder,
        fiyatı hesaplar ve kaydı onaylar.
        (kiralama_baslat karşılığı)
        """
        # Etkinliğe katılımcı eklemeyi dene
        basarili, mesaj = self._etkinlik.katilimci_ekle()
        if not basarili:
            return False, mesaj

        # Bilet türüne göre fiyat hesapla
        carpan = self.TUR_CARPAN.get(self._bilet_turu, 1.0)
        self._ucret = round(self._etkinlik.get_bilet_fiyati() * carpan, 2)

        return True, (
            f"✅ Bilet oluşturuldu!\n"
            f"   Bilet No  : #{self._bilet_id}\n"
            f"   Etkinlik  : {self._etkinlik.get_ad()}\n"
            f"   Katılımcı : {self._katilimci.get_ad()}\n"
            f"   Tür       : {self._bilet_turu.value}\n"
            f"   Ücret     : ₺{self._ucret:.2f}\n"
            f"   Tarih     : {self._kayit_tarihi.strftime('%d.%m.%Y %H:%M')}"
        )

    def bilet_iptal_et(self) -> tuple[bool, str]:
        """
        Bilet iptal eder, etkinlik kapasitesini serbest bırakır.
        (kiralama_bitir / Odeme.iptal_et karşılığı)
        """
        if self._iptal_mi:
            return False, f"Bilet #{self._bilet_id} zaten iptal edilmiş."

        self._iptal_mi     = True
        self._iptal_tarihi = datetime.now()
        self._etkinlik.katilimci_cikar()  # Kontenjanı geri ver

        return True, (
            f"🔴 Bilet #{self._bilet_id} iptal edildi.\n"
            f"   Etkinlik : {self._etkinlik.get_ad()}\n"
            f"   İptal    : {self._iptal_tarihi.strftime('%d.%m.%Y %H:%M')}"
        )

    def bilet_bilgisi(self) -> dict:
        """Bilet detaylarını sözlük olarak döndürür (kiralama_bilgisi karşılığı)"""
        return {
            "bilet_id":     self._bilet_id,
            "etkinlik_id":  self._etkinlik.get_etkinlik_id(),
            "etkinlik":     self._etkinlik.get_ad(),
            "katilimci":    self._katilimci.get_ad(),
            "email":        self._katilimci.get_email(),
            "tur":          self._bilet_turu.value,
            "ucret":        f"₺{self._ucret:.2f}",
            "kayit":        self._kayit_tarihi.strftime("%d.%m.%Y %H:%M"),
            "iptal_mi":     self._iptal_mi,
            "iptal_tarihi": self._iptal_tarihi.strftime("%d.%m.%Y %H:%M") if self._iptal_tarihi else "—"
        }

    def to_dict(self) -> dict:
        return {
            "bilet_id":      self._bilet_id,
            "etkinlik_id":   self._etkinlik.get_etkinlik_id(),
            "katilimci_id":  self._katilimci.get_katilimci_id(),
            "bilet_turu":    self._bilet_turu.name,
            "kayit_tarihi":  self._kayit_tarihi.isoformat(),
            "ucret":         self._ucret,
            "iptal_mi":      self._iptal_mi,
            "iptal_tarihi":  self._iptal_tarihi.isoformat() if self._iptal_tarihi else None
        }

    @classmethod
    def from_dict(cls, data: dict, etkinlik: Etkinlik, katilimci: Katilimci):
        b = cls(
            data["bilet_id"],
            etkinlik,
            katilimci,
            BiletTuru[data["bilet_turu"]]
        )
        b._kayit_tarihi = datetime.fromisoformat(data["kayit_tarihi"])
        b._ucret        = data.get("ucret", 0.0)
        b._iptal_mi     = data.get("iptal_mi", False)
        if data.get("iptal_tarihi"):
            b._iptal_tarihi = datetime.fromisoformat(data["iptal_tarihi"])
        return b

    def __repr__(self) -> str:
        durum = "İPTAL" if self._iptal_mi else "GEÇERLİ"
        return f"Bilet(#{self._bilet_id}, {durum}, {self._etkinlik.get_ad()})"


# ==================== RAPORLAMA ====================

class Rapor:
    """
    Sistem raporları ve istatistiklerini oluşturan sınıf.
    (Rapor sınıfının birebir karşılığı)
    """

    def __init__(self, sistem):
        self._sistem = sistem

    def katilim_raporu(self, etkinlik_id: str = None) -> dict:
        """
        Etkinlik bazlı katılım raporunu döndürür.
        (gelir_raporu karşılığı)
        """
        biletler = [b for b in self._sistem.get_tum_biletler() if not b.get_iptal_mi()]

        if etkinlik_id:
            biletler = [b for b in biletler
                        if b.get_etkinlik().get_etkinlik_id() == etkinlik_id]

        toplam_gelir = sum(b.get_ucret() for b in biletler)
        ort_ucret    = toplam_gelir / len(biletler) if biletler else 0

        return {
            "toplam_bilet":    len(biletler),
            "toplam_gelir":    f"₺{toplam_gelir:.2f}",
            "ortalama_ucret":  f"₺{ort_ucret:.2f}",
            "iptal_sayisi":    len([b for b in self._sistem.get_tum_biletler() if b.get_iptal_mi()])
        }

    def etkinlik_doluluk_raporu(self) -> list[dict]:
        """
        Her etkinliğin doluluk istatistiklerini döndürür.
        (arac_kullanim_raporu karşılığı)
        """
        rapor = []
        for etkinlik in self._sistem.get_etkinlikler().values():
            gecerli = [b for b in self._sistem.get_tum_biletler()
                       if b.get_etkinlik().get_etkinlik_id() == etkinlik.get_etkinlik_id()
                       and not b.get_iptal_mi()]
            gelir = sum(b.get_ucret() for b in gecerli)
            rapor.append({
                "etkinlik_id":     etkinlik.get_etkinlik_id(),
                "ad":              etkinlik.get_ad(),
                "tarih":           etkinlik.get_tarih().strftime("%d.%m.%Y"),
                "konum":           etkinlik.get_konum(),
                "kapasite":        etkinlik.get_kapasite(),
                "kayitli":         etkinlik.get_katilimci_sayisi(),
                "bos_koltuk":      etkinlik.get_bos_koltuk(),
                "doluluk":         f"%{etkinlik.doluluk_orani():.1f}",
                "gelir":           f"₺{gelir:.2f}",
                "kayit_durumu":    "Açık" if etkinlik.get_aktif_mi() else "Kapalı"
            })
        return rapor

    def sistem_ozeti(self) -> dict:
        """Tüm sistemin genel özet raporu (sistem_ozeti karşılığı)"""
        s = self._sistem
        tum_biletler   = s.get_tum_biletler()
        gecerli        = [b for b in tum_biletler if not b.get_iptal_mi()]
        toplam_gelir   = sum(b.get_ucret() for b in gecerli)

        return {
            "toplam_etkinlik":   len(s.get_etkinlikler()),
            "aktif_etkinlik":    len([e for e in s.get_etkinlikler().values() if e.get_aktif_mi()]),
            "toplam_katilimci":  len(s.get_katilimcilar()),
            "toplam_bilet":      len(tum_biletler),
            "gecerli_bilet":     len(gecerli),
            "iptal_bilet":       len(tum_biletler) - len(gecerli),
            "toplam_gelir":      f"₺{toplam_gelir:.2f}"
        }


# ==================== ANA SİSTEM ====================

class EtkinlikSistemi:
    """
    Etkinlik kayıt sisteminin ana yönetici sınıfı.
    Tüm işlemler bu sınıf üzerinden koordine edilir.
    (PaylasimSistemi sınıfının karşılığı)

    İç veri yapıları:
        _etkinlikler   → dict  { etkinlik_id: Etkinlik }
        _katilimcilar  → dict  { katilimci_id: Katilimci }
        _biletler      → list  [ Bilet ]
    """

    def __init__(self):
        self._etkinlikler:  dict[str, Etkinlik]   = {}
        self._katilimcilar: dict[str, Katilimci]  = {}
        self._biletler:     list[Bilet]            = []

        self._sonraki_bid: int = 1    # Bilet ID sayacı

    # ─── Veri Kalıcılığı (JSON) ───────────────────────────────

    def verileri_kaydet(self, dosya_adi: str = "etkinlik_data.json") -> bool:
        """Tüm sistem verisini JSON dosyasına yazar"""
        try:
            data = {
                "etkinlikler":  [e.to_dict() for e in self._etkinlikler.values()],
                "katilimcilar": [k.to_dict() for k in self._katilimcilar.values()],
                "biletler":     [b.to_dict() for b in self._biletler],
                "counters":     {"bid": self._sonraki_bid}
            }
            with open(dosya_adi, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    def verileri_yukle(self, dosya_adi: str = "etkinlik_data.json") -> bool:
        """JSON dosyasından sistem verisini yükler"""
        if not os.path.exists(dosya_adi):
            return False
        try:
            with open(dosya_adi, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._etkinlikler.clear()
            for d in data.get("etkinlikler", []):
                e = Etkinlik.from_dict(d)
                self._etkinlikler[e.get_etkinlik_id()] = e

            self._katilimcilar.clear()
            for d in data.get("katilimcilar", []):
                k = Katilimci.from_dict(d)
                self._katilimcilar[k.get_katilimci_id()] = k

            self._biletler.clear()
            for d in data.get("biletler", []):
                etkinlik   = self._etkinlikler.get(d["etkinlik_id"])
                katilimci  = self._katilimcilar.get(d["katilimci_id"])
                if etkinlik and katilimci:
                    b = Bilet.from_dict(d, etkinlik, katilimci)
                    self._biletler.append(b)
                    katilimci.bilet_ekle(b)

            self._sonraki_bid = data.get("counters", {}).get("bid", 1)
            return True
        except Exception:
            return False

    # ─── Etkinlik Yönetimi ────────────────────────────────────

    def etkinlik_ekle(self, etkinlik: Etkinlik) -> tuple[bool, str]:
        """Sisteme yeni etkinlik ekler (arac_ekle karşılığı)"""
        if etkinlik.get_etkinlik_id() in self._etkinlikler:
            return False, f"ID '{etkinlik.get_etkinlik_id()}' zaten kayıtlı."
        self._etkinlikler[etkinlik.get_etkinlik_id()] = etkinlik
        return True, f"✓ '{etkinlik.get_ad()}' etkinliği sisteme eklendi."

    def etkinlik_sil(self, etkinlik_id: str) -> tuple[bool, str]:
        """Etkinliği siler — aktif kayıtlı bilet varsa silmez (arac_sil karşılığı)"""
        if etkinlik_id not in self._etkinlikler:
            return False, "Etkinlik bulunamadı."

        aktif_bilet = [b for b in self._biletler
                       if b.get_etkinlik().get_etkinlik_id() == etkinlik_id
                       and not b.get_iptal_mi()]
        if aktif_bilet:
            return False, f"Bu etkinliğe {len(aktif_bilet)} geçerli bilet var. Önce iptal edin."

        ad = self._etkinlikler[etkinlik_id].get_ad()
        del self._etkinlikler[etkinlik_id]
        return True, f"✓ '{ad}' etkinliği sistemden silindi."

    def get_etkinlikler(self) -> dict[str, Etkinlik]:
        return self._etkinlikler.copy()

    def get_aktif_etkinlikler(self) -> dict[str, Etkinlik]:
        """Kaydı açık etkinlikleri döndürür (get_musait_araclar karşılığı)"""
        return {k: v for k, v in self._etkinlikler.items() if v.get_aktif_mi()}

    # ─── Katılımcı Yönetimi ───────────────────────────────────

    def katilimci_ekle(self, katilimci: Katilimci) -> tuple[bool, str]:
        """Sisteme yeni katılımcı kaydeder (kullanici_ekle karşılığı)"""
        if katilimci.get_katilimci_id() in self._katilimcilar:
            return False, f"ID '{katilimci.get_katilimci_id()}' zaten kayıtlı."

        for k in self._katilimcilar.values():
            if k.get_email() == katilimci.get_email():
                return False, "Bu e-posta adresi zaten kayıtlı."

        self._katilimcilar[katilimci.get_katilimci_id()] = katilimci
        return True, f"✓ '{katilimci.get_ad()}' katılımcı olarak kaydedildi."

    def katilimci_sil(self, katilimci_id: str) -> tuple[bool, str]:
        """Katılımcıyı siler — aktif bileti varsa silmez (kullanici_sil karşılığı)"""
        if katilimci_id not in self._katilimcilar:
            return False, "Katılımcı bulunamadı."

        k = self._katilimcilar[katilimci_id]
        if k.aktif_bilet():
            return False, f"'{k.get_ad()}' adlı katılımcının aktif bileti var."

        del self._katilimcilar[katilimci_id]
        return True, f"✓ '{k.get_ad()}' sistemden silindi."

    def get_katilimcilar(self) -> dict[str, Katilimci]:
        return self._katilimcilar.copy()

    # ─── Bilet Yönetimi ───────────────────────────────────────

    def bilet_olustur(self, etkinlik_id: str, katilimci_id: str,
                      bilet_turu: BiletTuru = BiletTuru.STANDART) -> tuple[bool, str]:
        """
        Yeni bilet oluşturur, tüm kontrolleri yapar.
        (kiralama_baslat karşılığı)
        """
        if etkinlik_id not in self._etkinlikler:
            return False, "Etkinlik bulunamadı."
        if katilimci_id not in self._katilimcilar:
            return False, "Katılımcı bulunamadı."

        etkinlik  = self._etkinlikler[etkinlik_id]
        katilimci = self._katilimcilar[katilimci_id]

        # Aynı etkinlik için zaten bileti var mı?
        if katilimci.aktif_bilet(etkinlik_id):
            return False, f"'{katilimci.get_ad()}' zaten bu etkinliğe kayıtlı."

        bilet = Bilet(self._sonraki_bid, etkinlik, katilimci, bilet_turu)
        self._sonraki_bid += 1

        basarili, mesaj = bilet.bilet_olustur()
        if basarili:
            self._biletler.append(bilet)
            katilimci.bilet_ekle(bilet)

        return basarili, mesaj

    def bilet_iptal_et(self, bilet_id: int) -> tuple[bool, str]:
        """Belirtilen bileti iptal eder (kiralama_bitir karşılığı)"""
        bilet = next((b for b in self._biletler
                      if b.get_bilet_id() == bilet_id and not b.get_iptal_mi()), None)
        if not bilet:
            return False, "Geçerli bilet bulunamadı veya zaten iptal edilmiş."
        return bilet.bilet_iptal_et()

    def get_tum_biletler(self) -> list[Bilet]:
        return list(self._biletler)

    def get_gecerli_biletler(self) -> list[Bilet]:
        """İptal edilmemiş biletleri döndürür"""
        return [b for b in self._biletler if not b.get_iptal_mi()]

    def get_iptal_biletler(self) -> list[Bilet]:
        return [b for b in self._biletler if b.get_iptal_mi()]

    def toplam_gelir(self) -> float:
        return sum(b.get_ucret() for b in self._biletler if not b.get_iptal_mi())

    # ─── Raporlama ────────────────────────────────────────────

    def rapor_olustur(self) -> Rapor:
        """Yeni Rapor nesnesi oluşturur"""
        return Rapor(self)

    def detayli_rapor(self) -> dict:
        """Hızlı sistem özeti döndürür"""
        return self.rapor_olustur().sistem_ozeti()

    def __len__(self) -> int:
        return len(self._etkinlikler)

    def __repr__(self) -> str:
        return (f"EtkinlikSistemi("
                f"etkinlik:{len(self._etkinlikler)}, "
                f"katilimci:{len(self._katilimcilar)}, "
                f"bilet:{len(self._biletler)})")


# ==================== KONSOL MENÜSÜ ====================

def yazdir_baslik(baslik: str) -> None:
    print("\n" + "═" * 58)
    print(f"   🎫  {baslik}")
    print("═" * 58)

def yazdir_ayrac() -> None:
    print("─" * 58)

def ana_menu() -> None:
    print("\n" + "═" * 58)
    print("           🎫  ETKİNLİK KAYIT SİSTEMİ")
    print("═" * 58)
    print("  ── Etkinlik İşlemleri ───────────────────────────")
    print("  1  ➜  Yeni etkinlik ekle")
    print("  2  ➜  Tüm etkinlikleri listele")
    print("  3  ➜  Etkinlik sil")
    print("  ── Katılımcı İşlemleri ───────────────────────────")
    print("  4  ➜  Yeni katılımcı kaydet")
    print("  5  ➜  Tüm katılımcıları listele")
    print("  ── Bilet İşlemleri ───────────────────────────────")
    print("  6  ➜  Bilet oluştur")
    print("  7  ➜  Bilet iptal et")
    print("  8  ➜  Tüm biletleri listele")
    print("  ── Raporlar ──────────────────────────────────────")
    print("  9  ➜  Sistem özeti")
    print("  10 ➜  Etkinlik doluluk raporu")
    print("  11 ➜  Katılım & gelir raporu")
    print("  ── Genel ─────────────────────────────────────────")
    print("  12 ➜  Verileri kaydet")
    print("  13 ➜  Verileri yükle")
    print("   0 ➜  Çıkış")
    print("═" * 58)


# ── Menü aksiyonları ────────────────────────────────────────

def etkinlik_ekle_menu(sistem: EtkinlikSistemi):
    yazdir_baslik("Yeni Etkinlik Ekle")
    eid    = input("  Etkinlik ID (örn. E001) : ").strip()
    ad     = input("  Etkinlik adı            : ").strip()
    tarih_str = input("  Tarih (GG.AA.YYYY SS:DD): ").strip()
    konum  = input("  Konum                   : ").strip()

    try:
        tarih = datetime.strptime(tarih_str, "%d.%m.%Y %H:%M")
    except ValueError:
        print("  [!] Geçersiz tarih formatı.")
        return

    try:
        kapasite = int(input("  Kapasite (kişi sayısı)  : ").strip())
        fiyat    = float(input("  Standart bilet ücreti ₺ : ").strip())
    except ValueError:
        print("  [!] Sayısal değer girilmeli.")
        return

    e = Etkinlik(eid, ad, tarih, konum, kapasite, fiyat)
    ok, msg = sistem.etkinlik_ekle(e)
    print(f"\n  {'✅' if ok else '❌'} {msg}")


def etkinlikleri_listele(sistem: EtkinlikSistemi):
    yazdir_baslik("Etkinlik Listesi")
    etkinlikler = sistem.get_etkinlikler()
    if not etkinlikler:
        print("  Henüz etkinlik eklenmedi.")
        return

    for e in etkinlikler.values():
        durum = "✅ Açık" if e.get_aktif_mi() else "🔒 Kapalı"
        print(f"\n  [{e.get_etkinlik_id()}] {e.get_ad()}")
        print(f"      📅 {e.get_tarih().strftime('%d.%m.%Y %H:%M')}  |  📍 {e.get_konum()}")
        print(f"      👥 {e.get_katilimci_sayisi()}/{e.get_kapasite()} kişi  |  "
              f"💺 {e.get_bos_koltuk()} boş  |  ₺{e.get_bilet_fiyati():.2f}  |  {durum}")


def etkinlik_sil_menu(sistem: EtkinlikSistemi):
    yazdir_baslik("Etkinlik Sil")
    eid = input("  Silinecek Etkinlik ID: ").strip()
    ok, msg = sistem.etkinlik_sil(eid)
    print(f"\n  {'✅' if ok else '❌'} {msg}")


def katilimci_ekle_menu(sistem: EtkinlikSistemi):
    yazdir_baslik("Yeni Katılımcı Kaydet")
    kid   = input("  Katılımcı ID (örn. K001) : ").strip()
    ad    = input("  Ad Soyad                  : ").strip()
    email = input("  E-posta                   : ").strip()
    tel   = input("  Telefon (opsiyonel)       : ").strip()

    k = Katilimci(kid, ad, email, tel)
    ok, msg = sistem.katilimci_ekle(k)
    print(f"\n  {'✅' if ok else '❌'} {msg}")


def katilimcilari_listele(sistem: EtkinlikSistemi):
    yazdir_baslik("Katılımcı Listesi")
    katilimcilar = sistem.get_katilimcilar()
    if not katilimcilar:
        print("  Henüz katılımcı eklenmedi.")
        return

    for k in katilimcilar.values():
        aktif_b = len([b for b in k.bilet_gecmisi() if not b.get_iptal_mi()])
        print(f"  [{k.get_katilimci_id()}] {k.get_ad():<25} "
              f"📧 {k.get_email():<30} "
              f"🎫 {aktif_b} bilet")


def bilet_olustur_menu(sistem: EtkinlikSistemi):
    yazdir_baslik("Bilet Oluştur")

    aktif = sistem.get_aktif_etkinlikler()
    if not aktif:
        print("  Kayıt açık etkinlik yok.")
        return

    print("  Kayıt Açık Etkinlikler:")
    for e in aktif.values():
        print(f"    [{e.get_etkinlik_id()}] {e.get_ad()} — "
              f"{e.get_bos_koltuk()} boş koltuk — ₺{e.get_bilet_fiyati():.2f}")

    eid = input("\n  Etkinlik ID : ").strip()
    kid = input("  Katılımcı ID: ").strip()

    print("\n  Bilet Türleri:")
    turler = list(BiletTuru)
    for i, t in enumerate(turler, 1):
        katsayi = Bilet.TUR_CARPAN[t]
        print(f"    {i}. {t.value} (×{katsayi})")

    try:
        secim = int(input("  Seçiminiz (varsayılan=1): ").strip() or "1") - 1
        bilet_turu = turler[secim]
    except (ValueError, IndexError):
        bilet_turu = BiletTuru.STANDART

    ok, msg = sistem.bilet_olustur(eid, kid, bilet_turu)
    print(f"\n  {'✅' if ok else '❌'}")
    print(msg)


def bilet_iptal_menu(sistem: EtkinlikSistemi):
    yazdir_baslik("Bilet İptal Et")
    gecerli = sistem.get_gecerli_biletler()
    if not gecerli:
        print("  Geçerli bilet yok.")
        return

    print("  Geçerli Biletler:")
    for b in gecerli:
        print(f"    #{b.get_bilet_id():>4} | {b.get_etkinlik().get_ad():<30} | "
              f"{b.get_katilimci().get_ad():<20} | ₺{b.get_ucret():.2f}")

    try:
        bid = int(input("\n  İptal edilecek Bilet ID: ").strip())
    except ValueError:
        print("  [!] Geçersiz bilet ID.")
        return

    ok, msg = sistem.bilet_iptal_et(bid)
    print(f"\n  {'✅' if ok else '❌'}")
    print(msg)


def biletleri_listele(sistem: EtkinlikSistemi):
    yazdir_baslik("Tüm Biletler")
    biletler = sistem.get_tum_biletler()
    if not biletler:
        print("  Henüz bilet oluşturulmadı.")
        return

    print(f"\n  {'ID':>4}  {'Etkinlik':<28} {'Katılımcı':<20} {'Tür':<12} {'Ücret':>8}  Durum")
    yazdir_ayrac()
    for b in biletler:
        durum = "🔴 İptal" if b.get_iptal_mi() else "🟢 Geçerli"
        print(f"  #{b.get_bilet_id():>3}  {b.get_etkinlik().get_ad():<28} "
              f"{b.get_katilimci().get_ad():<20} "
              f"{b.get_bilet_turu().value:<12} "
              f"₺{b.get_ucret():>7.2f}  {durum}")


def sistem_ozeti(sistem: EtkinlikSistemi):
    yazdir_baslik("Sistem Özeti")
    for k, v in sistem.detayli_rapor().items():
        print(f"  • {k:<25}: {v}")


def doluluk_raporu(sistem: EtkinlikSistemi):
    yazdir_baslik("Etkinlik Doluluk Raporu")
    rapor  = sistem.rapor_olustur()
    satirlar = rapor.etkinlik_doluluk_raporu()

    if not satirlar:
        print("  Etkinlik bulunamadı.")
        return

    for r in satirlar:
        print(f"\n  [{r['etkinlik_id']}] {r['ad']}")
        print(f"       📅 {r['tarih']}  |  📍 {r['konum']}")
        print(f"       👥 {r['kayitli']}/{r['kapasite']}  |  "
              f"Doluluk: {r['doluluk']}  |  "
              f"Gelir: {r['gelir']}  |  "
              f"Kayıt: {r['kayit_durumu']}")


def katilim_gelir_raporu(sistem: EtkinlikSistemi):
    yazdir_baslik("Katılım & Gelir Raporu")
    rapor = sistem.rapor_olustur().katilim_raporu()
    for k, v in rapor.items():
        print(f"  • {k:<25}: {v}")


# ==================== ANA DÖNGÜ (MAIN LOOP) ====================

def main():
    print("\n" + "═" * 58)
    print("     🎫  Etkinlik Kayıt Sistemi — Hoş Geldiniz!")
    print("═" * 58)

    sistem = EtkinlikSistemi()

    # Başlangıç verileri
    sistem.verileri_yukle()

    # Demo verisi
    if not sistem.get_etkinlikler():
        e1 = Etkinlik("E001", "Yapay Zeka Konferansı",
                      datetime(2026, 6, 15, 10, 0), "İstanbul Kongre Merkezi", 500, 250.0)
        e2 = Etkinlik("E002", "Python Workshop",
                      datetime(2026, 7, 1, 14, 0), "Ankara Teknopark", 50, 150.0)
        e3 = Etkinlik("E003", "Müzik Festivali",
                      datetime(2026, 8, 20, 18, 0), "İzmir Kültürpark", 2000, 180.0)
        for e in [e1, e2, e3]:
            sistem.etkinlik_ekle(e)

        k1 = Katilimci("K001", "Ahmet Yılmaz",  "ahmet@mail.com",  "05551234567")
        k2 = Katilimci("K002", "Ayşe Demir",    "ayse@mail.com",   "05559876543")
        k3 = Katilimci("K003", "Mehmet Kaya",   "mehmet@mail.com", "")
        for k in [k1, k2, k3]:
            sistem.katilimci_ekle(k)

        sistem.bilet_olustur("E001", "K001", BiletTuru.VIP)
        sistem.bilet_olustur("E001", "K002", BiletTuru.STANDART)
        sistem.bilet_olustur("E002", "K003", BiletTuru.OGRENCI)

        print("  ✅ Demo verisi yüklendi.\n")

    MENU = {
        "1":  etkinlik_ekle_menu,
        "2":  etkinlikleri_listele,
        "3":  etkinlik_sil_menu,
        "4":  katilimci_ekle_menu,
        "5":  katilimcilari_listele,
        "6":  bilet_olustur_menu,
        "7":  bilet_iptal_menu,
        "8":  biletleri_listele,
        "9":  sistem_ozeti,
        "10": doluluk_raporu,
        "11": katilim_gelir_raporu,
    }

    while True:
        ana_menu()
        secim = input("\n  Seçiminiz: ").strip()

        if secim == "0":
            kaydet = input("\n  Çıkmadan önce kaydet? (e/h): ").strip().lower()
            if kaydet == "e":
                ok = sistem.verileri_kaydet()
                print("  ✅ Kaydedildi." if ok else "  ❌ Kayıt hatası.")
            print("\n  Güle güle! 🎫\n")
            break
        elif secim == "12":
            ok = sistem.verileri_kaydet()
            print(f"\n  {'✅ Veriler kaydedildi.' if ok else '❌ Kayıt başarısız.'}")
        elif secim == "13":
            ok = sistem.verileri_yukle()
            print(f"\n  {'✅ Veriler yüklendi.' if ok else '❌ Dosya bulunamadı.'}")
        elif secim in MENU:
            MENU[secim](sistem)
        else:
            print("  [!] Geçersiz seçim. 0-13 arası bir sayı girin.")

        input("\n  ↩  Devam etmek için Enter'a basın...")


if __name__ == "__main__":
    main()
