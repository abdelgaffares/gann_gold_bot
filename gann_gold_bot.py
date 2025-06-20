# -*- coding: utf-8 -*-
"""نظام جان الذكي اللحظي للذهب - إصدار نهائي مدمج مع الحاسبة"""

import requests
import time
import math
import csv
from datetime import datetime, timedelta

# إعدادات عامة
SYMBOL = "XAU/USD"
API_KEY = "d5b4c49f39f441c9984d2cc11db35452"
TELEGRAM_BOT = "7819220266:AAGmzSsd-n61qXU0F7oxOqauwpvwTTZPX6Y"
TELEGRAM_CHAT = "@saxo_copy"
PERCENTAGES = [0.088, 0.09375, 0.104, 0.1125, 0.125]
TOUCH_MARGIN = 1.0
ZONES_COUNT = 5
DAYS_TO_ANALYZE = 7
INTERVAL_MINUTES = 5

# ========== الحاسبة الذكية ==========
def get_daily_data():
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": "1day",
        "outputsize": DAYS_TO_ANALYZE + 1,
        "apikey": API_KEY
    }
    r = requests.get(url, params=params)
    data = r.json()
    if "values" not in data:
        raise Exception("❌ فشل جلب البيانات اليومية.")
    return [dict(date=x["datetime"], high=float(x["high"]), low=float(x["low"]), close=float(x["close"])) for x in data["values"]]

def get_live_price():
    url = f"https://api.twelvedata.com/price?symbol={SYMBOL}&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()
    if "price" not in data:
        raise Exception("❌ فشل الحصول على السعر الحي.")
    return float(data["price"])

def choose_best_percentage(high, low, history):
    def score_pct(pct):
        diff = high - low
        levels = [round(high - diff * pct * i, 2) for i in range(1, ZONES_COUNT+1)]
        levels += [round(low + diff * pct * i, 2) for i in range(1, ZONES_COUNT+1)]
        score = 0
        for candle in history[1:]:
            for lvl in levels:
                if candle["low"] - TOUCH_MARGIN <= lvl <= candle["high"] + TOUCH_MARGIN:
                    score += 1
        return score
    return max(PERCENTAGES, key=score_pct)

def get_level_strength(level, history):
    touches = 0
    for candle in history[1:]:
        if (
            abs(candle["high"] - level) <= TOUCH_MARGIN or
            abs(candle["low"] - level) <= TOUCH_MARGIN or
            abs(candle["close"] - level) <= TOUCH_MARGIN
        ):
            touches += 1
    return touches

def format_strength(touches):
    if touches >= 3:
        return "🔥 x3+"
    elif touches == 2:
        return "💪 x2"
    elif touches == 1:
        return "💪 x1"
    return "👀 جديدة"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# ========== نظام جان الذكي ==========
class GannSmartSystem:
    def __init__(self, pivot_price, pivot_time, strong_levels):
        self.pivot_price = pivot_price
        self.pivot_time = pivot_time
        self.strong_levels = strong_levels
        self.last_hour_alert = None

    def calculate_levels(self):
        root = math.sqrt(self.pivot_price)
        return {
            'دعم 45°': round(self.pivot_price - root, 2),
            'مقاومة 45°': round(self.pivot_price + root, 2),
            'مقاومة 90°': round(self.pivot_price + root * 2, 2),
            'مقاومة 180°': round(self.pivot_price + root * 4, 2),
            'مقاومة 360°': round(self.pivot_price + root * 8, 2)
        }

    def calculate_angles(self, count):
        base = math.sqrt(self.pivot_price)
        return {
            'زاوية 1x1': round(self.pivot_price + base * count / 180, 2),
            'زاوية -1x1': round(self.pivot_price - base * count / 180, 2),
            'زاوية 2x1': round(self.pivot_price + base * count / 90, 2),
            'زاوية -2x1': round(self.pivot_price - base * count / 90, 2),
        }

    def monitor(self):
        send_telegram("🚀 بدء نظام جان الذكي اللحظي للذهب...")
        while True:
            try:
                price = get_live_price()
                now = datetime.now()
                count = int((now - self.pivot_time).total_seconds() / (INTERVAL_MINUTES * 60))
                angles = self.calculate_angles(count)
                levels = self.calculate_levels()
                signals = []

                for name, val in {**angles, **levels}.items():
                    if abs(price - val) <= 0.5 and val in self.strong_levels:
                        signals.append(f"{name} عند {val}")

                if len(signals) >= 2:
                    direction = "🚨 شراء" if price < self.pivot_price else "⚠️ بيع"
                    msg = f"{direction} سكالب محتمل للذهب\n\n💵 السعر: {price:.2f}\n🕒 {now.strftime('%Y-%m-%d %H:%M')}\n📌 إشارات:\n- " + "\n- ".join(signals)
                    send_telegram(msg)
                    time.sleep(300)

                if not self.last_hour_alert or (now - self.last_hour_alert).seconds >= 3600:
                    send_telegram(f"⌛ النظام يعمل - {now.strftime('%H:%M')}")
                    self.last_hour_alert = now

                time.sleep(INTERVAL_MINUTES * 60)
            except Exception as e:
                print(f"❌ خطأ في المراقبة: {e}")
                time.sleep(60)

# ========== تشغيل مدمج ==========
def run_combined():
    try:
        data = get_daily_data()
        high = max(x["high"] for x in data)
        low = min(x["low"] for x in data)
        price = get_live_price()
        best_pct = choose_best_percentage(high, low, data)
        diff = high - low

        strong_levels = set()
        msg = f"📊 *حاسبة جان الذكية - تقييم القوة الكاملة*\n💰 السعر الحي: {price:.2f}\n🔺 القمة: {high:.2f}\n🔻 القاع: {low:.2f}\n📐 النسبة الذكية المختارة: *{best_pct*100:.3f}%*\n\n"
        msg += "🔻 *من القمة (هبوط):*\n"
        for i in range(1, ZONES_COUNT+1):
            lvl = round(high - diff * best_pct * i, 2)
            touches = get_level_strength(lvl, data)
            strength = format_strength(touches)
            msg += f"- منطقة {i}: {lvl} ← {strength}\n"
            if "💪" in strength or "🔥" in strength:
                strong_levels.add(lvl)

        msg += "\n🔺 *من القاع (صعود):*\n"
        for i in range(1, ZONES_COUNT+1):
            lvl = round(low + diff * best_pct * i, 2)
            touches = get_level_strength(lvl, data)
            strength = format_strength(touches)
            msg += f"- منطقة {i}: {lvl} ← {strength}\n"
            if "💪" in strength or "🔥" in strength:
                strong_levels.add(lvl)

        msg += f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_telegram(msg)

        system = GannSmartSystem(price, datetime.now(), strong_levels)
        system.monitor()
    except Exception as e:
        print(f"❌ فشل التشغيل الكامل: {e}")

# ========== نقطة التشغيل ==========
if __name__ == "__main__":
    run_combined()
