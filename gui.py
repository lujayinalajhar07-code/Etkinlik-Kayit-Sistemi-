"""
╔══════════════════════════════════════════════════════════════╗
║   🎫  ETKİNLİK KAYIT SİSTEMİ — Ultra-Modern PyQt5 GUI      ║
║   Glassmorphism + Dark Futuristic Aesthetic                  ║
║   Requires: PyQt5                                            ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import math
from datetime import datetime
from enum import Enum
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QStackedWidget,
    QGridLayout, QSpacerItem, QDialog, QDateTimeEdit, QSpinBox,
    QDoubleSpinBox, QMessageBox, QProgressBar, QScrollBar
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QPoint, QSize, pyqtSignal, QThread, QDateTime,
    QParallelAnimationGroup
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QPainter, QLinearGradient,
    QRadialGradient, QPixmap, QBrush, QPen, QFontDatabase,
    QConicalGradient, QPolygon, QIcon, QCursor
)


# ═══════════════════════════════════════════════════════════════
#  BACKEND CLASSES (inline — no external import needed)
# ═══════════════════════════════════════════════════════════════

class BiletTuru(Enum):
    STANDART = "Standart"
    VIP      = "VIP"
    OGRENCI  = "Öğrenci"
    GRUP     = "Grup"


class Etkinlik:
    def __init__(self, etkinlik_id, ad, tarih, konum, kapasite, bilet_fiyati):
        self._etkinlik_id      = etkinlik_id
        self._ad               = ad
        self._tarih            = tarih
        self._konum            = konum
        self._kapasite         = kapasite
        self._bilet_fiyati     = bilet_fiyati
        self._aktif_mi         = True
        self._katilimci_sayisi = 0

    def get_etkinlik_id(self):    return self._etkinlik_id
    def get_ad(self):             return self._ad
    def get_tarih(self):          return self._tarih
    def get_konum(self):          return self._konum
    def get_kapasite(self):       return self._kapasite
    def get_bilet_fiyati(self):   return self._bilet_fiyati
    def get_aktif_mi(self):       return self._aktif_mi
    def get_katilimci_sayisi(self): return self._katilimci_sayisi
    def get_bos_koltuk(self):     return self._kapasite - self._katilimci_sayisi

    def kayit_durumu_guncelle(self, aktif):
        self._aktif_mi = aktif

    def katilimci_ekle(self):
        if not self._aktif_mi:
            return False, f"'{self._ad}' için kayıt kapalı."
        if self._katilimci_sayisi >= self._kapasite:
            return False, f"'{self._ad}' doldu!"
        self._katilimci_sayisi += 1
        return True, "OK"

    def katilimci_cikar(self):
        if self._katilimci_sayisi > 0:
            self._katilimci_sayisi -= 1

    def doluluk_orani(self):
        return (self._katilimci_sayisi / self._kapasite * 100) if self._kapasite else 0


class Katilimci:
    def __init__(self, katilimci_id, ad, email, telefon=""):
        self._katilimci_id = katilimci_id
        self._ad           = ad
        self._email        = email
        self._telefon      = telefon
        self._biletler     = []

    def get_katilimci_id(self): return self._katilimci_id
    def get_ad(self):           return self._ad
    def get_email(self):        return self._email
    def get_telefon(self):      return self._telefon

    def bilet_ekle(self, b):    self._biletler.append(b)
    def bilet_gecmisi(self):    return list(self._biletler)

    def aktif_bilet(self, etkinlik_id=None):
        for b in self._biletler:
            if b.get_iptal_mi(): continue
            if etkinlik_id is None or b.get_etkinlik().get_etkinlik_id() == etkinlik_id:
                return b
        return None


class Bilet:
    TUR_CARPAN = {
        BiletTuru.STANDART: 1.0,
        BiletTuru.VIP:      2.5,
        BiletTuru.OGRENCI:  0.5,
        BiletTuru.GRUP:     0.8,
    }

    def __init__(self, bilet_id, etkinlik, katilimci, bilet_turu=BiletTuru.STANDART):
        self._bilet_id     = bilet_id
        self._etkinlik     = etkinlik
        self._katilimci    = katilimci
        self._bilet_turu   = bilet_turu
        self._kayit_tarihi = datetime.now()
        self._ucret        = 0.0
        self._iptal_mi     = False
        self._iptal_tarihi = None

    def get_bilet_id(self):     return self._bilet_id
    def get_etkinlik(self):     return self._etkinlik
    def get_katilimci(self):    return self._katilimci
    def get_bilet_turu(self):   return self._bilet_turu
    def get_kayit_tarihi(self): return self._kayit_tarihi
    def get_ucret(self):        return self._ucret
    def get_iptal_mi(self):     return self._iptal_mi

    def bilet_olustur(self):
        ok, msg = self._etkinlik.katilimci_ekle()
        if not ok: return False, msg
        self._ucret = round(self._etkinlik.get_bilet_fiyati() * self.TUR_CARPAN[self._bilet_turu], 2)
        return True, f"Bilet #{self._bilet_id} oluşturuldu. Ücret: ₺{self._ucret:.2f}"

    def bilet_iptal_et(self):
        if self._iptal_mi: return False, "Zaten iptal edilmiş."
        self._iptal_mi     = True
        self._iptal_tarihi = datetime.now()
        self._etkinlik.katilimci_cikar()
        return True, f"Bilet #{self._bilet_id} iptal edildi."


class EtkinlikSistemi:
    def __init__(self):
        self._etkinlikler  = {}
        self._katilimcilar = {}
        self._biletler     = []
        self._sonraki_bid  = 1

    def etkinlik_ekle(self, e):
        if e.get_etkinlik_id() in self._etkinlikler:
            return False, "ID zaten mevcut."
        self._etkinlikler[e.get_etkinlik_id()] = e
        return True, f"'{e.get_ad()}' eklendi."

    def etkinlik_sil(self, eid):
        if eid not in self._etkinlikler: return False, "Bulunamadı."
        aktif = [b for b in self._biletler
                 if b.get_etkinlik().get_etkinlik_id() == eid and not b.get_iptal_mi()]
        if aktif: return False, f"{len(aktif)} aktif bilet var."
        ad = self._etkinlikler[eid].get_ad()
        del self._etkinlikler[eid]
        return True, f"'{ad}' silindi."

    def get_etkinlikler(self):       return self._etkinlikler.copy()
    def get_aktif_etkinlikler(self): return {k:v for k,v in self._etkinlikler.items() if v.get_aktif_mi()}

    def katilimci_ekle(self, k):
        if k.get_katilimci_id() in self._katilimcilar: return False, "ID mevcut."
        for u in self._katilimcilar.values():
            if u.get_email() == k.get_email(): return False, "E-posta kayıtlı."
        self._katilimcilar[k.get_katilimci_id()] = k
        return True, f"'{k.get_ad()}' kaydedildi."

    def katilimci_sil(self, kid):
        if kid not in self._katilimcilar: return False, "Bulunamadı."
        k = self._katilimcilar[kid]
        if k.aktif_bilet(): return False, "Aktif bileti var."
        del self._katilimcilar[kid]
        return True, f"'{k.get_ad()}' silindi."

    def get_katilimcilar(self): return self._katilimcilar.copy()

    def bilet_olustur(self, eid, kid, tur=BiletTuru.STANDART):
        if eid not in self._etkinlikler: return False, "Etkinlik yok."
        if kid not in self._katilimcilar: return False, "Katılımcı yok."
        e = self._etkinlikler[eid]
        k = self._katilimcilar[kid]
        if k.aktif_bilet(eid): return False, "Zaten kayıtlı."
        b = Bilet(self._sonraki_bid, e, k, tur)
        self._sonraki_bid += 1
        ok, msg = b.bilet_olustur()
        if ok:
            self._biletler.append(b)
            k.bilet_ekle(b)
        return ok, msg

    def bilet_iptal_et(self, bid):
        b = next((x for x in self._biletler if x.get_bilet_id() == bid and not x.get_iptal_mi()), None)
        if not b: return False, "Bilet bulunamadı."
        return b.bilet_iptal_et()

    def get_tum_biletler(self):    return list(self._biletler)
    def get_gecerli_biletler(self): return [b for b in self._biletler if not b.get_iptal_mi()]

    def toplam_gelir(self):
        return sum(b.get_ucret() for b in self._biletler if not b.get_iptal_mi())

    def ozet(self):
        return {
            "Toplam Etkinlik":  len(self._etkinlikler),
            "Aktif Etkinlik":   len(self.get_aktif_etkinlikler()),
            "Katılımcı":        len(self._katilimcilar),
            "Geçerli Bilet":    len(self.get_gecerli_biletler()),
            "Toplam Gelir":     f"₺{self.toplam_gelir():,.0f}",
        }


# ═══════════════════════════════════════════════════════════════
#  DESIGN TOKENS — DARK FUTURISTIC GLASSMORPHISM
# ═══════════════════════════════════════════════════════════════

BG_DEEP    = "#050811"
BG_MID     = "#090e1a"
BG_SURFACE = "#0d1424"

GLASS_BG   = "rgba(13, 20, 36, 0.7)"
GLASS_BDR  = "rgba(99, 179, 237, 0.15)"

CYAN       = "#38bdf8"
CYAN_DIM   = "#0ea5e9"
CYAN_GLOW  = "#7dd3fc"
VIOLET     = "#818cf8"
VIOLET_DIM = "#6366f1"
ROSE       = "#f43f5e"
EMERALD    = "#10b981"
AMBER      = "#f59e0b"

TEXT_PRI   = "#e2e8f0"
TEXT_SEC   = "#94a3b8"
TEXT_MUTED = "#475569"

GRAD_CYAN  = f"qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {CYAN},stop:1 {VIOLET})"
GRAD_ROSE  = f"qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ROSE},stop:1 {AMBER})"
GRAD_GRN   = f"qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {EMERALD},stop:1 {CYAN})"


# ═══════════════════════════════════════════════════════════════
#  ANIMATED BACKGROUND CANVAS
# ═══════════════════════════════════════════════════════════════

class AnimatedBG(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)

    def _tick(self):
        self._t += 0.012
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Deep space gradient background
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor("#050811"))
        bg.setColorAt(0.5, QColor("#07101f"))
        bg.setColorAt(1.0, QColor("#050811"))
        p.fillRect(self.rect(), bg)

        # Animated orbs
        orbs = [
            (0.18, 0.22, 320, QColor(56, 189, 248, 28),  math.sin(self._t * 0.7) * 40),
            (0.75, 0.35, 280, QColor(129, 140, 248, 22), math.cos(self._t * 0.5) * 50),
            (0.50, 0.80, 380, QColor(16, 185, 129, 18),  math.sin(self._t * 0.4 + 1) * 35),
            (0.88, 0.72, 200, QColor(244, 63, 94, 20),   math.cos(self._t * 0.9 + 2) * 30),
        ]
        for rx, ry, r, col, dy in orbs:
            cx = int(w * rx)
            cy = int(h * ry + dy)
            grad = QRadialGradient(cx, cy, r)
            grad.setColorAt(0.0, col)
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Grid lines (subtle)
        pen = QPen(QColor(56, 189, 248, 12))
        pen.setWidth(1)
        p.setPen(pen)
        grid_size = 60
        for x in range(0, w, grid_size):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            p.drawLine(0, y, w, y)

        p.end()


# ═══════════════════════════════════════════════════════════════
#  GLASS CARD WIDGET
# ═══════════════════════════════════════════════════════════════

class GlassCard(QFrame):
    def __init__(self, parent=None, accent=None):
        super().__init__(parent)
        self._accent = accent or QColor(56, 189, 248)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._setup_style()
        self._add_shadow()

    def _setup_style(self):
        self.setStyleSheet(f"""
            GlassCard {{
                background: rgba(13, 22, 42, 0.72);
                border: 1px solid rgba(56, 189, 248, 0.18);
                border-radius: 18px;
            }}
        """)

    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(56, 189, 248, 30))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Top accent line
        pen = QPen(self._accent)
        pen.setWidth(2)
        p.setPen(pen)
        p.drawLine(30, 0, self.width() - 30, 0)
        p.end()


# ═══════════════════════════════════════════════════════════════
#  NEON BUTTON
# ═══════════════════════════════════════════════════════════════

class NeonButton(QPushButton):
    def __init__(self, text, color=CYAN, parent=None):
        super().__init__(text, parent)
        self._color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self._base_style(False)

    def _base_style(self, hovered):
        alpha = "55" if hovered else "22"
        border_alpha = "cc" if hovered else "88"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self._color}{alpha};
                color: {self._color};
                border: 1px solid {self._color}{border_alpha};
                border-radius: 10px;
                padding: 0 22px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }}
        """)

    def enterEvent(self, e):
        self._base_style(True)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(self._color))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def leaveEvent(self, e):
        self._base_style(False)
        self.setGraphicsEffect(None)


class DangerButton(NeonButton):
    def __init__(self, text, parent=None):
        super().__init__(text, ROSE, parent)


class SuccessButton(NeonButton):
    def __init__(self, text, parent=None):
        super().__init__(text, EMERALD, parent)


# ═══════════════════════════════════════════════════════════════
#  GLASS INPUT
# ═══════════════════════════════════════════════════════════════

INPUT_STYLE = f"""
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {{
        background: rgba(8, 14, 28, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 10px;
        padding: 10px 14px;
        color: {TEXT_PRI};
        font-size: 13px;
        min-height: 20px;
        selection-background-color: rgba(56, 189, 248, 0.3);
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
    QDoubleSpinBox:focus, QDateTimeEdit:focus {{
        border: 1px solid {CYAN};
        background: rgba(56, 189, 248, 0.06);
    }}
    QLineEdit::placeholder {{ color: {TEXT_MUTED}; }}
    QComboBox::drop-down {{ border: none; width: 28px; }}
    QComboBox::down-arrow {{
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {CYAN};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: {BG_SURFACE};
        border: 1px solid rgba(56, 189, 248, 0.25);
        color: {TEXT_PRI};
        selection-background-color: rgba(56, 189, 248, 0.2);
        border-radius: 8px;
        padding: 4px;
    }}
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 20px;
    }}
    QDateTimeEdit::up-button, QDateTimeEdit::down-button {{
        background: transparent;
        border: none;
    }}
"""

TABLE_STYLE = f"""
    QTableWidget {{
        background: transparent;
        border: none;
        gridline-color: rgba(56, 189, 248, 0.08);
        color: {TEXT_PRI};
        font-size: 13px;
        outline: none;
    }}
    QTableWidget::item {{
        padding: 12px 16px;
        border-bottom: 1px solid rgba(56, 189, 248, 0.06);
    }}
    QTableWidget::item:selected {{
        background: rgba(56, 189, 248, 0.15);
        color: {CYAN_GLOW};
    }}
    QHeaderView::section {{
        background: rgba(56, 189, 248, 0.08);
        color: {CYAN};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 10px 16px;
        border: none;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        text-transform: uppercase;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 4px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(56, 189, 248, 0.3);
        border-radius: 2px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""


# ═══════════════════════════════════════════════════════════════
#  STAT CARD
# ═══════════════════════════════════════════════════════════════

class StatCard(QWidget):
    def __init__(self, label, value, icon, color, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedHeight(110)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 22px; background: transparent;")
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignCenter)
        top.addWidget(icon_lbl)
        top.addStretch()

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 28px;
            font-weight: 800;
            background: transparent;
            letter-spacing: -0.5px;
        """)
        top.addWidget(self.val_lbl)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")

        lay.addLayout(top)
        lay.addWidget(lbl)

    def setValue(self, v):
        self.val_lbl.setText(str(v))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Glass bg
        p.setPen(Qt.NoPen)
        glass = QColor(13, 22, 42, 180)
        p.setBrush(glass)
        p.drawRoundedRect(self.rect(), 16, 16)

        # Colored border
        pen = QPen(QColor(self._color.red(), self._color.green(), self._color.blue(), 60))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(0,0,-1,-1), 16, 16)

        # Top accent
        pen2 = QPen(self._color)
        pen2.setWidth(2)
        p.setPen(pen2)
        p.drawLine(20, 1, self.width() - 20, 1)

        p.end()


# ═══════════════════════════════════════════════════════════════
#  NAV RAIL BUTTON
# ═══════════════════════════════════════════════════════════════

class NavRailButton(QPushButton):
    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self._icon_t = icon_text
        self._label  = label
        self._active = False
        self.setCheckable(True)
        self.setFixedSize(72, 72)
        self.setCursor(Qt.PointingHandCursor)
        self._update()

    def setActive(self, v):
        self._active = v
        self._update()

    def _update(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(56, 189, 248, 0.15);
                    border: 1px solid rgba(56, 189, 248, 0.5);
                    border-radius: 16px;
                    color: {CYAN};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 16px;
                    color: {TEXT_MUTED};
                }}
                QPushButton:hover {{
                    background: rgba(56, 189, 248, 0.07);
                    border-color: rgba(56, 189, 248, 0.2);
                    color: {TEXT_SEC};
                }}
            """)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = CYAN if self._active else TEXT_MUTED

        # Icon
        font = QFont()
        font.setPointSize(18)
        p.setFont(font)
        p.setPen(QColor(color))
        p.drawText(QRect(0, 8, self.width(), 32), Qt.AlignCenter, self._icon_t)

        # Label
        font2 = QFont()
        font2.setPointSize(7)
        font2.setWeight(QFont.DemiBold)
        p.setFont(font2)
        p.drawText(QRect(0, 42, self.width(), 20), Qt.AlignCenter, self._label)
        p.end()


# ═══════════════════════════════════════════════════════════════
#  TOAST NOTIFICATION
# ═══════════════════════════════════════════════════════════════

class Toast(QFrame):
    def __init__(self, msg, kind="success", parent=None):
        super().__init__(parent)
        c = {
            "success": EMERALD,
            "error":   ROSE,
            "info":    CYAN,
        }.get(kind, CYAN)

        self.setFixedHeight(52)
        self.setMinimumWidth(320)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(9, 16, 32, 0.95);
                border: 1px solid {c}66;
                border-left: 3px solid {c};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(c))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)

        icons = {"success": "✓", "error": "✕", "info": "ℹ"}
        dot = QLabel(icons.get(kind, "•"))
        dot.setStyleSheet(f"color: {c}; font-size: 15px; font-weight: 800; background: transparent;")
        dot.setFixedWidth(22)

        txt = QLabel(msg)
        txt.setStyleSheet(f"color: {TEXT_PRI}; font-size: 13px; background: transparent;")
        txt.setWordWrap(True)

        lay.addWidget(dot)
        lay.addWidget(txt)


# ═══════════════════════════════════════════════════════════════
#  FORM LABEL
# ═══════════════════════════════════════════════════════════════

def make_label(text, size=11, color=TEXT_SEC, bold=False):
    lbl = QLabel(text)
    w = 700 if bold else 400
    lbl.setStyleSheet(f"""
        color: {color};
        font-size: {size}px;
        font-weight: {w};
        background: transparent;
        letter-spacing: 0.5px;
    """)
    return lbl


def section_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {TEXT_PRI};
        font-size: 18px;
        font-weight: 800;
        background: transparent;
        letter-spacing: -0.3px;
    """)
    return lbl


def make_input(placeholder=""):
    w = QLineEdit()
    w.setPlaceholderText(placeholder)
    w.setStyleSheet(INPUT_STYLE)
    w.setMinimumHeight(44)
    return w


def make_combo(items):
    w = QComboBox()
    w.addItems(items)
    w.setStyleSheet(INPUT_STYLE)
    w.setMinimumHeight(44)
    return w


def sep_line():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background: rgba(56,189,248,0.1); border: none; max-height: 1px;")
    return f


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD PAGE
# ═══════════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    def __init__(self, sistem: EtkinlikSistemi):
        super().__init__()
        self.sistem = sistem
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(24)

        # Header
        hdr = QHBoxLayout()
        left = QVBoxLayout(); left.setSpacing(4)
        title = QLabel("DASHBOARD")
        title.setStyleSheet(f"""
            color: {TEXT_PRI};
            font-size: 26px;
            font-weight: 900;
            background: transparent;
            letter-spacing: 3px;
        """)
        sub = make_label("Etkinlik Kayıt Sistemi — Genel Bakış", 13, TEXT_SEC)
        left.addWidget(title)
        left.addWidget(sub)
        hdr.addLayout(left)
        hdr.addStretch()

        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet(f"""
            color: {CYAN};
            font-size: 13px;
            font-weight: 600;
            background: rgba(56,189,248,0.08);
            border: 1px solid rgba(56,189,248,0.2);
            border-radius: 8px;
            padding: 6px 14px;
        """)
        hdr.addWidget(self.clock_lbl)
        timer = QTimer(self)
        timer.timeout.connect(self._update_clock)
        timer.start(1000)
        self._update_clock()

        lay.addLayout(hdr)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self._stats = [
            StatCard("Toplam Etkinlik",   "0", "🎪", CYAN,    self),
            StatCard("Aktif Etkinlik",    "0", "✅", EMERALD, self),
            StatCard("Katılımcı",         "0", "👤", VIOLET,  self),
            StatCard("Geçerli Bilet",     "0", "🎫", AMBER,   self),
            StatCard("Toplam Gelir",      "₺0","💰", ROSE,    self),
        ]
        for sc in self._stats:
            stats_row.addWidget(sc)
        lay.addLayout(stats_row)

        # Two-column bottom
        bottom = QHBoxLayout()
        bottom.setSpacing(20)

        # Events list card
        ev_card = GlassCard(self)
        ev_lay  = QVBoxLayout(ev_card)
        ev_lay.setContentsMargins(24, 20, 24, 20)
        ev_lay.setSpacing(14)
        ev_lay.addWidget(make_label("AKTİF ETKİNLİKLER", 11, CYAN, True))
        ev_lay.addWidget(sep_line())
        self._ev_list_lay = QVBoxLayout()
        self._ev_list_lay.setSpacing(8)
        ev_lay.addLayout(self._ev_list_lay)
        ev_lay.addStretch()
        bottom.addWidget(ev_card, 3)

        # Bilet type breakdown card
        bk_card = GlassCard(self, QColor(VIOLET))
        bk_lay  = QVBoxLayout(bk_card)
        bk_lay.setContentsMargins(24, 20, 24, 20)
        bk_lay.setSpacing(14)
        bk_lay.addWidget(make_label("BİLET DAĞILIMI", 11, VIOLET, True))
        bk_lay.addWidget(sep_line())
        self._bk_bars_lay = QVBoxLayout()
        self._bk_bars_lay.setSpacing(12)
        bk_lay.addLayout(self._bk_bars_lay)
        bk_lay.addStretch()
        bottom.addWidget(bk_card, 2)

        lay.addLayout(bottom)

    def _update_clock(self):
        self.clock_lbl.setText(datetime.now().strftime("  %H:%M:%S  |  %d.%m.%Y  "))

    def refresh(self):
        ozet = self.sistem.ozet()
        vals = list(ozet.values())
        for i, sc in enumerate(self._stats):
            sc.setValue(vals[i])

        # Events
        while self._ev_list_lay.count():
            item = self._ev_list_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        etkinlikler = list(self.sistem.get_aktif_etkinlikler().values())[:5]
        if not etkinlikler:
            self._ev_list_lay.addWidget(make_label("Aktif etkinlik yok.", 13, TEXT_MUTED))
        for e in etkinlikler:
            row = QHBoxLayout()
            dot = QLabel("◆")
            dot.setStyleSheet(f"color: {CYAN}; font-size: 10px; background: transparent;")
            name = make_label(e.get_ad(), 13, TEXT_PRI)
            pct  = make_label(f"%{e.doluluk_orani():.0f} dolu", 12, TEXT_SEC)
            row.addWidget(dot)
            row.addWidget(name)
            row.addStretch()
            row.addWidget(pct)
            w = QWidget(); w.setStyleSheet("background: transparent;")
            w.setLayout(row)
            self._ev_list_lay.addWidget(w)

        # Bilet bars
        while self._bk_bars_lay.count():
            item = self._bk_bars_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        biletler = self.sistem.get_gecerli_biletler()
        turler   = {}
        for b in biletler:
            t = b.get_bilet_turu().value
            turler[t] = turler.get(t, 0) + 1

        colors = [CYAN, VIOLET, EMERALD, AMBER]
        total  = max(len(biletler), 1)
        for i, (t, c) in enumerate(turler.items()):
            pct = c / total
            col = colors[i % len(colors)]

            row_lay = QVBoxLayout(); row_lay.setSpacing(4)
            top_row = QHBoxLayout()
            top_row.addWidget(make_label(t, 12, TEXT_PRI))
            top_row.addStretch()
            top_row.addWidget(make_label(f"{c}", 12, col, True))

            bar_bg  = QFrame()
            bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet(f"background: rgba(255,255,255,0.06); border-radius: 3px;")

            bar_fill = QFrame(bar_bg)
            bar_fill.setFixedHeight(6)
            fill_w = max(int(pct * 180), 6)
            bar_fill.setFixedWidth(fill_w)
            bar_fill.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {col}, stop:1 {col}88);
                border-radius: 3px;
            """)

            row_lay.addLayout(top_row)
            row_lay.addWidget(bar_bg)
            w = QWidget(); w.setStyleSheet("background: transparent;")
            w.setLayout(row_lay)
            self._bk_bars_lay.addWidget(w)

        if not turler:
            self._bk_bars_lay.addWidget(make_label("Henüz bilet yok.", 13, TEXT_MUTED))


# ═══════════════════════════════════════════════════════════════
#  EVENTS PAGE
# ═══════════════════════════════════════════════════════════════

class EtkinlikPage(QWidget):
    toast_signal = pyqtSignal(str, str)

    def __init__(self, sistem: EtkinlikSistemi):
        super().__init__()
        self.sistem = sistem
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(24)

        # Title
        top = QHBoxLayout()
        top.addWidget(section_title("ETKİNLİKLER"))
        top.addStretch()
        outer.addLayout(top)

        # Split: form | table
        split = QHBoxLayout()
        split.setSpacing(20)

        # ── ADD FORM ──
        form_card = GlassCard(self)
        form_card.setFixedWidth(320)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(22, 20, 22, 22)
        fl.setSpacing(12)

        fl.addWidget(make_label("YENİ ETKİNLİK", 11, CYAN, True))
        fl.addWidget(sep_line())

        fl.addWidget(make_label("Etkinlik ID"))
        self.e_id    = make_input("E001")
        fl.addWidget(self.e_id)

        fl.addWidget(make_label("Etkinlik Adı"))
        self.e_ad    = make_input("Konser / Konferans...")
        fl.addWidget(self.e_ad)

        fl.addWidget(make_label("Konum"))
        self.e_konum = make_input("İstanbul Kongre Merkezi")
        fl.addWidget(self.e_konum)

        fl.addWidget(make_label("Tarih & Saat"))
        self.e_tarih = QDateTimeEdit()
        self.e_tarih.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.e_tarih.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.e_tarih.setStyleSheet(INPUT_STYLE)
        self.e_tarih.setMinimumHeight(44)
        fl.addWidget(self.e_tarih)

        row2 = QHBoxLayout(); row2.setSpacing(10)
        kleft = QVBoxLayout()
        kleft.addWidget(make_label("Kapasite"))
        self.e_kap = QSpinBox()
        self.e_kap.setRange(1, 100000)
        self.e_kap.setValue(200)
        self.e_kap.setStyleSheet(INPUT_STYLE)
        self.e_kap.setMinimumHeight(44)
        kleft.addWidget(self.e_kap)
        row2.addLayout(kleft)

        kright = QVBoxLayout()
        kright.addWidget(make_label("Bilet Fiyatı ₺"))
        self.e_fiy = QDoubleSpinBox()
        self.e_fiy.setRange(0, 999999)
        self.e_fiy.setValue(150.0)
        self.e_fiy.setDecimals(2)
        self.e_fiy.setStyleSheet(INPUT_STYLE)
        self.e_fiy.setMinimumHeight(44)
        kright.addWidget(self.e_fiy)
        row2.addLayout(kright)
        fl.addLayout(row2)

        fl.addStretch()

        add_btn = NeonButton("＋  Etkinlik Ekle")
        add_btn.clicked.connect(self._add)
        fl.addWidget(add_btn)

        split.addWidget(form_card)

        # ── TABLE ──
        table_card = GlassCard(self)
        tl = QVBoxLayout(table_card)
        tl.setContentsMargins(0, 20, 0, 0)
        tl.setSpacing(14)

        th = QHBoxLayout()
        th.setContentsMargins(24, 0, 24, 0)
        th.addWidget(make_label("TÜM ETKİNLİKLER", 11, CYAN, True))
        th.addStretch()
        refresh_btn = NeonButton("↺  Yenile")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh)
        th.addWidget(refresh_btn)
        tl.addLayout(th)
        tl.addWidget(sep_line())

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID","ETKİNLİK","KONUM","TARİH","KAPASİTE","DOLULUK","DURUM"])
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(False)
        self.table.setFocusPolicy(Qt.NoFocus)

        # Delete row
        del_row = QHBoxLayout()
        del_row.setContentsMargins(24, 0, 24, 14)
        del_row.addStretch()
        del_btn = DangerButton("✕  Seçili Sil")
        del_btn.setFixedWidth(140)
        del_btn.clicked.connect(self._delete)
        del_row.addWidget(del_btn)

        tl.addWidget(self.table)
        tl.addLayout(del_row)

        split.addWidget(table_card)
        outer.addLayout(split)
        self.refresh()

    def refresh(self):
        etkinlikler = list(self.sistem.get_etkinlikler().values())
        self.table.setRowCount(len(etkinlikler))
        for r, e in enumerate(etkinlikler):
            self.table.setRowHeight(r, 52)
            items = [
                (e.get_etkinlik_id(), CYAN),
                (e.get_ad(), TEXT_PRI),
                (e.get_konum(), TEXT_SEC),
                (e.get_tarih().strftime("%d.%m.%Y %H:%M"), TEXT_SEC),
                (f"{e.get_katilimci_sayisi()}/{e.get_kapasite()}", TEXT_PRI),
                (f"%{e.doluluk_orani():.0f}", AMBER if e.doluluk_orani() > 70 else TEXT_PRI),
                ("✅ Açık" if e.get_aktif_mi() else "🔒 Kapalı",
                 EMERALD if e.get_aktif_mi() else ROSE),
            ]
            for c, (txt, col) in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(col))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if c == 0:
                    item.setFont(QFont("Courier New", 11, QFont.Bold))
                self.table.setItem(r, c, item)

    def _add(self):
        eid   = self.e_id.text().strip()
        ad    = self.e_ad.text().strip()
        konum = self.e_konum.text().strip()
        if not eid or not ad or not konum:
            self.toast_signal.emit("Tüm alanları doldurun.", "error"); return
        qt = self.e_tarih.dateTime()
        tarih = datetime(qt.date().year(), qt.date().month(), qt.date().day(),
                         qt.time().hour(), qt.time().minute())
        e = Etkinlik(eid, ad, tarih, konum, self.e_kap.value(), self.e_fiy.value())
        ok, msg = self.sistem.etkinlik_ekle(e)
        self.toast_signal.emit(msg, "success" if ok else "error")
        if ok:
            self.e_id.clear(); self.e_ad.clear(); self.e_konum.clear()
            self.refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.toast_signal.emit("Bir satır seçin.", "error"); return
        eid = self.table.item(row, 0).text()
        ok, msg = self.sistem.etkinlik_sil(eid)
        self.toast_signal.emit(msg, "success" if ok else "error")
        if ok: self.refresh()


# ═══════════════════════════════════════════════════════════════
#  ATTENDEES PAGE
# ═══════════════════════════════════════════════════════════════

class KatilimciPage(QWidget):
    toast_signal = pyqtSignal(str, str)

    def __init__(self, sistem: EtkinlikSistemi):
        super().__init__()
        self.sistem = sistem
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(24)
        outer.addWidget(section_title("KATILIMCILAR"))

        split = QHBoxLayout(); split.setSpacing(20)

        # Form card
        form_card = GlassCard(self, QColor(VIOLET))
        form_card.setFixedWidth(300)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(22, 20, 22, 22)
        fl.setSpacing(12)

        fl.addWidget(make_label("YENİ KATILIMCI", 11, VIOLET, True))
        fl.addWidget(sep_line())

        for lbl, attr, ph in [
            ("Katılımcı ID", "k_id",    "K001"),
            ("Ad Soyad",     "k_ad",    "Ahmet Yılmaz"),
            ("E-posta",      "k_email", "ahmet@mail.com"),
            ("Telefon",      "k_tel",   "0555 000 0000"),
        ]:
            fl.addWidget(make_label(lbl))
            inp = make_input(ph)
            setattr(self, attr, inp)
            fl.addWidget(inp)

        fl.addStretch()
        add_btn = NeonButton("＋  Katılımcı Ekle", VIOLET)
        add_btn.clicked.connect(self._add)
        fl.addWidget(add_btn)
        split.addWidget(form_card)

        # Table card
        table_card = GlassCard(self, QColor(VIOLET))
        tl = QVBoxLayout(table_card)
        tl.setContentsMargins(0, 20, 0, 0)
        tl.setSpacing(14)

        th = QHBoxLayout(); th.setContentsMargins(24, 0, 24, 0)
        th.addWidget(make_label("KATILIMCI LİSTESİ", 11, VIOLET, True))
        th.addStretch()
        tl.addLayout(th)
        tl.addWidget(sep_line())

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","AD SOYAD","E-POSTA","TELEFON","AKTİF BİLET"])
        self.table.setStyleSheet(TABLE_STYLE.replace(CYAN, VIOLET))
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setFocusPolicy(Qt.NoFocus)

        del_row = QHBoxLayout(); del_row.setContentsMargins(24, 0, 24, 14)
        del_row.addStretch()
        del_btn = DangerButton("✕  Seçili Sil")
        del_btn.setFixedWidth(140)
        del_btn.clicked.connect(self._delete)
        del_row.addWidget(del_btn)

        tl.addWidget(self.table)
        tl.addLayout(del_row)
        split.addWidget(table_card)
        outer.addLayout(split)
        self.refresh()

    def refresh(self):
        katilimcilar = list(self.sistem.get_katilimcilar().values())
        self.table.setRowCount(len(katilimcilar))
        for r, k in enumerate(katilimcilar):
            self.table.setRowHeight(r, 52)
            aktif = len([b for b in k.bilet_gecmisi() if not b.get_iptal_mi()])
            items = [
                (k.get_katilimci_id(), VIOLET),
                (k.get_ad(),           TEXT_PRI),
                (k.get_email(),        TEXT_SEC),
                (k.get_telefon() or "—", TEXT_MUTED),
                (f"🎫 {aktif}",        AMBER if aktif else TEXT_MUTED),
            ]
            for c, (txt, col) in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(col))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if c == 0: item.setFont(QFont("Courier New", 11, QFont.Bold))
                self.table.setItem(r, c, item)

    def _add(self):
        kid   = self.k_id.text().strip()
        ad    = self.k_ad.text().strip()
        email = self.k_email.text().strip()
        tel   = self.k_tel.text().strip()
        if not kid or not ad or not email:
            self.toast_signal.emit("ID, ad ve e-posta zorunlu.", "error"); return
        k  = Katilimci(kid, ad, email, tel)
        ok, msg = self.sistem.katilimci_ekle(k)
        self.toast_signal.emit(msg, "success" if ok else "error")
        if ok:
            self.k_id.clear(); self.k_ad.clear(); self.k_email.clear(); self.k_tel.clear()
            self.refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            self.toast_signal.emit("Bir satır seçin.", "error"); return
        kid = self.table.item(row, 0).text()
        ok, msg = self.sistem.katilimci_sil(kid)
        self.toast_signal.emit(msg, "success" if ok else "error")
        if ok: self.refresh()


# ═══════════════════════════════════════════════════════════════
#  TICKETS PAGE
# ═══════════════════════════════════════════════════════════════

class BiletPage(QWidget):
    toast_signal = pyqtSignal(str, str)

    def __init__(self, sistem: EtkinlikSistemi):
        super().__init__()
        self.sistem = sistem
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(24)
        outer.addWidget(section_title("BİLETLER"))

        split = QHBoxLayout(); split.setSpacing(20)

        # Form card
        form_card = GlassCard(self, QColor(EMERALD))
        form_card.setFixedWidth(300)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(22, 20, 22, 22)
        fl.setSpacing(12)

        fl.addWidget(make_label("BİLET OLUŞTUR", 11, EMERALD, True))
        fl.addWidget(sep_line())

        fl.addWidget(make_label("Etkinlik"))
        self.b_etkinlik = make_combo([])
        fl.addWidget(self.b_etkinlik)

        fl.addWidget(make_label("Katılımcı"))
        self.b_katilimci = make_combo([])
        fl.addWidget(self.b_katilimci)

        fl.addWidget(make_label("Bilet Türü"))
        self.b_tur = make_combo([t.value for t in BiletTuru])
        fl.addWidget(self.b_tur)

        # Price preview
        self.price_lbl = QLabel("Tahmini ücret: —")
        self.price_lbl.setStyleSheet(f"""
            color: {EMERALD};
            font-size: 13px;
            font-weight: 600;
            background: rgba(16,185,129,0.08);
            border: 1px solid rgba(16,185,129,0.2);
            border-radius: 8px;
            padding: 8px 12px;
        """)
        self.b_tur.currentTextChanged.connect(self._update_price)
        self.b_etkinlik.currentTextChanged.connect(self._update_price)
        fl.addWidget(self.price_lbl)

        fl.addStretch()
        create_btn = SuccessButton("＋  Bilet Oluştur")
        create_btn.clicked.connect(self._create)
        fl.addWidget(create_btn)

        cancel_btn = DangerButton("✕  Seçili İptal Et")
        cancel_btn.clicked.connect(self._cancel)
        fl.addWidget(cancel_btn)

        split.addWidget(form_card)

        # Table
        table_card = GlassCard(self, QColor(EMERALD))
        tl = QVBoxLayout(table_card)
        tl.setContentsMargins(0, 20, 0, 0)
        tl.setSpacing(14)

        th = QHBoxLayout(); th.setContentsMargins(24, 0, 24, 0)
        th.addWidget(make_label("BİLET KAYITLARI", 11, EMERALD, True))
        th.addStretch()
        tl.addLayout(th)
        tl.addWidget(sep_line())

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["#","ETKİNLİK","KATILIMCI","TÜR","ÜCRET","KAYIT TARİHİ","DURUM"])
        self.table.setStyleSheet(TABLE_STYLE.replace(CYAN, EMERALD))
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setFocusPolicy(Qt.NoFocus)

        tl.addWidget(self.table)
        split.addWidget(table_card)
        outer.addLayout(split)
        self.refresh()

    def refresh(self):
        # Populate combos
        self.b_etkinlik.clear()
        for e in self.sistem.get_aktif_etkinlikler().values():
            self.b_etkinlik.addItem(f"{e.get_etkinlik_id()} — {e.get_ad()}", e.get_etkinlik_id())

        self.b_katilimci.clear()
        for k in self.sistem.get_katilimcilar().values():
            self.b_katilimci.addItem(f"{k.get_katilimci_id()} — {k.get_ad()}", k.get_katilimci_id())

        # Table
        biletler = self.sistem.get_tum_biletler()
        self.table.setRowCount(len(biletler))
        for r, b in enumerate(reversed(biletler)):
            self.table.setRowHeight(r, 52)
            durum_col = ROSE if b.get_iptal_mi() else EMERALD
            items = [
                (f"#{b.get_bilet_id():03d}",          EMERALD),
                (b.get_etkinlik().get_ad(),             TEXT_PRI),
                (b.get_katilimci().get_ad(),            TEXT_SEC),
                (b.get_bilet_turu().value,              AMBER),
                (f"₺{b.get_ucret():.2f}",              TEXT_PRI),
                (b.get_kayit_tarihi().strftime("%d.%m.%Y %H:%M"), TEXT_MUTED),
                ("✕ İptal" if b.get_iptal_mi() else "✓ Geçerli", durum_col),
            ]
            for c, (txt, col) in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(col))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if c == 0: item.setFont(QFont("Courier New", 11, QFont.Bold))
                self.table.setItem(r, c, item)
        self._update_price()

    def _update_price(self):
        eid = self.b_etkinlik.currentData()
        tur_txt = self.b_tur.currentText()
        if not eid:
            self.price_lbl.setText("Tahmini ücret: —"); return
        e = self.sistem.get_etkinlikler().get(eid)
        if not e: return
        tur_map = {t.value: t for t in BiletTuru}
        tur  = tur_map.get(tur_txt, BiletTuru.STANDART)
        katsayi = Bilet.TUR_CARPAN[tur]
        ucret = e.get_bilet_fiyati() * katsayi
        self.price_lbl.setText(f"Tahmini ücret: ₺{ucret:.2f}")

    def _create(self):
        eid = self.b_etkinlik.currentData()
        kid = self.b_katilimci.currentData()
        tur_txt = self.b_tur.currentText()
        if not eid or not kid:
            self.toast_signal.emit("Etkinlik ve katılımcı seçin.", "error"); return
        tur_map = {t.value: t for t in BiletTuru}
        tur = tur_map.get(tur_txt, BiletTuru.STANDART)
        ok, msg = self.sistem.bilet_olustur(eid, kid, tur)
        self.toast_signal.emit(msg, "success" if ok else "error")
        if ok: self.refresh()

    def _cancel(self):
        row = self.table.currentRow()
        if row < 0:
            self.toast_signal.emit("Bir satır seçin.", "error"); return
        bid_txt = self.table.item(row, 0).text().lstrip("#")
        try:
            bid = int(bid_txt)
        except ValueError:
            self.toast_signal.emit("Geçersiz bilet.", "error"); return
        ok, msg = self.sistem.bilet_iptal_et(bid)
        self.toast_signal.emit(msg, "success" if ok else "error")
        if ok: self.refresh()


# ═══════════════════════════════════════════════════════════════
#  REPORTS PAGE
# ═══════════════════════════════════════════════════════════════

class RaporPage(QWidget):
    def __init__(self, sistem: EtkinlikSistemi):
        super().__init__()
        self.sistem = sistem
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(24)
        outer.addWidget(section_title("RAPORLAR"))

        # Two rows of cards
        row1 = QHBoxLayout(); row1.setSpacing(16)

        # Genel ozet
        c1 = GlassCard(self, QColor(CYAN))
        l1 = QVBoxLayout(c1)
        l1.setContentsMargins(22,20,22,20); l1.setSpacing(10)
        l1.addWidget(make_label("SİSTEM ÖZETİ", 11, CYAN, True))
        l1.addWidget(sep_line())
        self._ozet_lay = QVBoxLayout(); self._ozet_lay.setSpacing(6)
        l1.addLayout(self._ozet_lay)
        l1.addStretch()
        row1.addWidget(c1)

        # Etkinlik doluluk
        c2 = GlassCard(self, QColor(VIOLET))
        l2 = QVBoxLayout(c2)
        l2.setContentsMargins(22,20,22,20); l2.setSpacing(10)
        l2.addWidget(make_label("ETKİNLİK DOLULUĞU", 11, VIOLET, True))
        l2.addWidget(sep_line())
        self._doluluk_lay = QVBoxLayout(); self._doluluk_lay.setSpacing(10)
        l2.addLayout(self._doluluk_lay)
        l2.addStretch()
        row1.addWidget(c2)

        # Gelir by tur
        c3 = GlassCard(self, QColor(ROSE))
        l3 = QVBoxLayout(c3)
        l3.setContentsMargins(22,20,22,20); l3.setSpacing(10)
        l3.addWidget(make_label("BİLET TÜRÜ GELİRİ", 11, ROSE, True))
        l3.addWidget(sep_line())
        self._gelir_lay = QVBoxLayout(); self._gelir_lay.setSpacing(8)
        l3.addLayout(self._gelir_lay)
        l3.addStretch()
        row1.addWidget(c3)

        outer.addLayout(row1)
        outer.addStretch()
        self.refresh()

    def refresh(self):
        ozet = self.sistem.ozet()
        while self._ozet_lay.count():
            item = self._ozet_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        colors = [CYAN, EMERALD, VIOLET, AMBER, ROSE]
        for i, (k, v) in enumerate(ozet.items()):
            row = QHBoxLayout()
            row.addWidget(make_label(k, 12, TEXT_SEC))
            row.addStretch()
            row.addWidget(make_label(str(v), 14, colors[i % len(colors)], True))
            w = QWidget(); w.setStyleSheet("background:transparent;"); w.setLayout(row)
            self._ozet_lay.addWidget(w)

        # Doluluk
        while self._doluluk_lay.count():
            item = self._doluluk_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for e in list(self.sistem.get_etkinlikler().values())[:5]:
            pct = e.doluluk_orani() / 100
            col = ROSE if pct > 0.8 else (AMBER if pct > 0.5 else EMERALD)

            vlay = QVBoxLayout(); vlay.setSpacing(4)
            top  = QHBoxLayout()
            top.addWidget(make_label(e.get_ad(), 12, TEXT_PRI))
            top.addStretch()
            top.addWidget(make_label(f"%{e.doluluk_orani():.0f}", 12, col, True))

            bar_bg = QFrame(); bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet("background: rgba(255,255,255,0.06); border-radius:3px;")
            bar_fill = QFrame(bar_bg); bar_fill.setFixedHeight(6)
            bar_fill.setFixedWidth(max(int(pct * 220), 4))
            bar_fill.setStyleSheet(f"background: {col}; border-radius:3px;")

            vlay.addLayout(top)
            vlay.addWidget(bar_bg)
            w = QWidget(); w.setStyleSheet("background:transparent;"); w.setLayout(vlay)
            self._doluluk_lay.addWidget(w)

        if not self.sistem.get_etkinlikler():
            self._doluluk_lay.addWidget(make_label("Etkinlik yok.", 13, TEXT_MUTED))

        # Gelir by tur
        while self._gelir_lay.count():
            item = self._gelir_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        gelir_tur = {}
        for b in self.sistem.get_gecerli_biletler():
            t = b.get_bilet_turu().value
            gelir_tur[t] = gelir_tur.get(t, 0) + b.get_ucret()

        turler_colors = [CYAN, VIOLET, EMERALD, AMBER]
        for i, (tur, gelir) in enumerate(gelir_tur.items()):
            col = turler_colors[i % len(turler_colors)]
            row = QHBoxLayout()
            row.addWidget(make_label(tur, 12, TEXT_SEC))
            row.addStretch()
            row.addWidget(make_label(f"₺{gelir:,.0f}", 13, col, True))
            w = QWidget(); w.setStyleSheet("background:transparent;"); w.setLayout(row)
            self._gelir_lay.addWidget(w)

        if not gelir_tur:
            self._gelir_lay.addWidget(make_label("Gelir verisi yok.", 13, TEXT_MUTED))


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sistem = EtkinlikSistemi()
        self._seed_data()

        self.setWindowTitle("🎫  Etkinlik Kayıt Sistemi")
        self.setMinimumSize(1280, 780)
        self.resize(1400, 860)
        self.setStyleSheet(f"QMainWindow {{ background: {BG_DEEP}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        root_lay = QHBoxLayout(central)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── ANIMATED BG ──
        self._bg = AnimatedBG(central)
        self._bg.setGeometry(0, 0, 1400, 860)
        self._bg.lower()

        # ── NAV RAIL ──
        rail = QWidget()
        rail.setFixedWidth(88)
        rail.setStyleSheet(f"""
            QWidget {{
                background: rgba(5, 8, 17, 0.92);
                border-right: 1px solid rgba(56,189,248,0.1);
            }}
        """)
        rail_lay = QVBoxLayout(rail)
        rail_lay.setContentsMargins(8, 20, 8, 20)
        rail_lay.setSpacing(6)
        rail_lay.setAlignment(Qt.AlignTop)

        # Logo
        logo_lbl = QLabel("🎫")
        logo_lbl.setStyleSheet(f"""
            font-size: 26px;
            background: rgba(56,189,248,0.12);
            border: 1px solid rgba(56,189,248,0.3);
            border-radius: 14px;
            padding: 6px;
        """)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setFixedSize(56, 56)
        rail_lay.addWidget(logo_lbl, alignment=Qt.AlignHCenter)

        # Divider
        d = QFrame(); d.setFrameShape(QFrame.HLine)
        d.setStyleSheet(f"background: rgba(56,189,248,0.12); border:none; max-height:1px; margin: 10px 6px;")
        rail_lay.addWidget(d)

        nav_items = [
            ("⬡",  "GENEL",       0),
            ("⬡",  "ETKİNLİK",   1),
            ("⬡",  "ÜYELER",      2),
            ("⬡",  "BİLETLER",   3),
            ("⬡",  "RAPORLAR",   4),
        ]
        nav_icons  = ["◈", "◉", "◎", "◆", "▣"]

        self._nav_btns = []
        for i, (ico, lbl, idx) in enumerate(nav_items):
            btn = NavRailButton(nav_icons[i], lbl)
            btn.clicked.connect(lambda _, ix=idx: self._go_to(ix))
            self._nav_btns.append(btn)
            rail_lay.addWidget(btn, alignment=Qt.AlignHCenter)

        rail_lay.addStretch()

        root_lay.addWidget(rail)

        # ── CONTENT AREA ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")

        self._dash_page  = DashboardPage(self.sistem)
        self._event_page = EtkinlikPage(self.sistem)
        self._att_page   = KatilimciPage(self.sistem)
        self._tick_page  = BiletPage(self.sistem)
        self._rep_page   = RaporPage(self.sistem)

        for page in [self._dash_page, self._event_page, self._att_page,
                     self._tick_page, self._rep_page]:
            self._stack.addWidget(page)
            if hasattr(page, 'toast_signal'):
                page.toast_signal.connect(self._show_toast)

        root_lay.addWidget(self._stack)

        self._toasts = []
        self._go_to(0)

        # Resize bg on window resize
        self.resizeEvent = self._on_resize

    def _on_resize(self, e):
        self._bg.setGeometry(0, 0, self.width(), self.height())

    def _go_to(self, idx):
        for i, btn in enumerate(self._nav_btns):
            btn.setActive(i == idx)
        self._stack.setCurrentIndex(idx)

        # Refresh data
        if idx == 0:  self._dash_page.refresh()
        if idx == 1:  self._event_page.refresh()
        if idx == 2:  self._att_page.refresh()
        if idx == 3:  self._tick_page.refresh()
        if idx == 4:  self._rep_page.refresh()

    def _show_toast(self, msg, kind="info"):
        toast = Toast(msg, kind, self)
        toast.show()
        toast.adjustSize()

        # Stack toasts
        y_base = self.height() - 70
        for t in self._toasts:
            y_base -= t.height() + 10

        toast.move(self.width() - toast.width() - 24, y_base)
        toast.raise_()
        self._toasts.append(toast)

        QTimer.singleShot(3000, lambda: self._remove_toast(toast))

    def _remove_toast(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
        toast.deleteLater()

    def _seed_data(self):
        events = [
            ("E001","Yapay Zeka Konferansı",  datetime(2026,6,15,10,0), "İstanbul Kongre", 500, 250.0),
            ("E002","Python Workshop",         datetime(2026,7,1,14,0),  "Ankara Teknopark", 50, 150.0),
            ("E003","Müzik Festivali",         datetime(2026,8,20,18,0), "İzmir Kültürpark", 2000, 180.0),
            ("E004","Robotik Yarışması",       datetime(2026,9,5,9,0),   "Bursa Expo", 300, 75.0),
        ]
        for args in events:
            self.sistem.etkinlik_ekle(Etkinlik(*args))

        members = [
            ("K001","Ahmet Yılmaz",   "ahmet@mail.com",   "05551234567"),
            ("K002","Ayşe Demir",     "ayse@mail.com",    "05559876543"),
            ("K003","Mehmet Kaya",    "mehmet@mail.com",  ""),
            ("K004","Zeynep Arslan",  "zeynep@mail.com",  "05554445566"),
        ]
        for args in members:
            self.sistem.katilimci_ekle(Katilimci(*args))

        tickets = [
            ("E001","K001",BiletTuru.VIP),
            ("E001","K002",BiletTuru.STANDART),
            ("E002","K003",BiletTuru.OGRENCI),
            ("E003","K004",BiletTuru.GRUP),
            ("E003","K001",BiletTuru.VIP),
        ]
        for eid, kid, tur in tickets:
            self.sistem.bilet_olustur(eid, kid, tur)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._bg.setGeometry(0, 0, self.width(), self.height())


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Etkinlik Kayıt Sistemi")

    # Dark palette base
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(BG_DEEP))
    pal.setColor(QPalette.WindowText,      QColor(TEXT_PRI))
    pal.setColor(QPalette.Base,            QColor(BG_SURFACE))
    pal.setColor(QPalette.Text,            QColor(TEXT_PRI))
    pal.setColor(QPalette.Button,          QColor(BG_MID))
    pal.setColor(QPalette.ButtonText,      QColor(TEXT_PRI))
    pal.setColor(QPalette.Highlight,       QColor(CYAN))
    pal.setColor(QPalette.HighlightedText, QColor(BG_DEEP))
    app.setPalette(pal)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()