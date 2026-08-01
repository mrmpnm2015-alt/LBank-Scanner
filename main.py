import ccxt
import time
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar

class CryptoScannerApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=5, padding=10)
        
        header = Label(
            text='📊 اسکنر لحظه‌ای فیوچرز LBank',
            size_hint_y=None,
            height=40,
            font_size='18sp',
            bold=True,
            halign='center'
        )
        
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        
        self.result_label = Label(
            text='🔍 آماده اسکن لحظه‌ای\nبرای شروع کلیک کنید',
            size_hint_y=None,
            height=450,
            halign='left',
            valign='top',
            font_size='11sp'
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        
        scan_btn = Button(
            text='🚀 اسکن لحظه‌ای',
            size_hint_y=None,
            height=60,
            background_color=(0.1, 0.5, 0.8, 1),
            font_size='14sp'
        )
        scan_btn.bind(on_press=self.scan_markets)
        
        self.status_label = Label(
            text='✅ آماده اسکن',
            size_hint_y=None,
            height=25,
            font_size='10sp',
            color=(0.6, 0.8, 0.6, 1)
        )
        
        scroll = ScrollView()
        scroll.add_widget(self.result_label)
        
        layout.add_widget(header)
        layout.add_widget(self.progress)
        layout.add_widget(scroll)
        layout.add_widget(scan_btn)
        layout.add_widget(self.status_label)
        return layout
    
    def load_previous_signals(self):
        try:
            if os.path.exists('previous_signals.json'):
                with open('previous_signals.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'symbols': [], 'timestamp': ''}
    
    def save_signals(self, symbols):
        try:
            with open('previous_signals.json', 'w') as f:
                json.dump({
                    'symbols': symbols,
                    'timestamp': datetime.now().isoformat()
                }, f)
        except:
            pass
    
    def calculate_ema(self, prices, period=50):
        if len(prices) < period:
            return None
        return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]
    
    def calculate_macd_precise(self, prices):
        if len(prices) < 26:
            return 'neutral', 0
        
        df = pd.Series(prices)
        exp1 = df.ewm(span=12, adjust=False).mean()
        exp2 = df.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        if len(histogram) < 3:
            return 'neutral', 0
        
        current = histogram.iloc[-1]
        prev = histogram.iloc[-2]
        
        if prev < 0 and current > 0:
            return 'strong_bullish', current
        if prev > 0 and current < 0:
            return 'strong_bearish', current
        
        return 'neutral', current
    
    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        if loss.iloc[-1] == 0:
            return 100
        rs = gain.iloc[-1] / loss.iloc[-1]
        return 100 - (100 / (1 + rs))
    
    def scan_markets(self, instance):
        self.result_label.text = "⏳ در حال اسکن..."
        self.progress.value = 0
        self.status_label.text = "⏳ اتصال به LBank..."
        
        def scan_async(dt):
            try:
                exchange = ccxt.lbank({
                    'options': {'defaultType': 'swap'},
                    'enableRateLimit': True,
                    'timeout': 30000
                })
                
                markets = exchange.load_markets()
                symbols = [s for s in markets.keys() 
                          if '/USDT' in s and markets[s].get('swap', False)]
                
                symbols = symbols[:80]
                results = []
                previous_signals = self.load_previous_signals()
                prev_symbols = set(previous_signals.get('symbols', []))
                
                total = len(symbols)
                
                for i, symbol in enumerate(symbols):
                    self.progress.value = (i / total) * 100
                    self.status_label.text = f"⏳ بررسی {i+1}/{total}: {symbol}"
                    
                    try:
                        ohlcv_h1 = exchange.fetch_ohlcv(symbol, '1h', limit=100)
                        if len(ohlcv_h1) < 60:
                            continue
                        
                        closes_h1 = [candle[4] for candle in ohlcv_h1]
                        last_price_h1 = closes_h1[-1]
                        ema50_h1 = self.calculate_ema(closes_h1)
                        
                        if ema50_h1 is None:
                            continue
                        
                        if last_price_h1 > ema50_h1 * 1.005:
                            trend = 'LONG'
                        elif last_price_h1 < ema50_h1 * 0.995:
                            trend = 'SHORT'
                        else:
                            continue
                        
                        ohlcv_m15 = exchange.fetch_ohlcv(symbol, '15m', limit=100)
                        if len(ohlcv_m15) < 60:
                            continue
                        
                        closes_m15 = [candle[4] for candle in ohlcv_m15]
                        last_price_m15 = closes_m15[-1]
                        ema50_m15 = self.calculate_ema(closes_m15)
                        
                        if ema50_m15 is None:
                            continue
                        
                        if trend == 'LONG' and last_price_m15 <= ema50_m15:
                            continue
                        if trend == 'SHORT' and last_price_m15 >= ema50_m15:
                            continue
                        
                        rsi = self.calculate_rsi(closes_m15)
                        
                        if trend == 'LONG' and rsi <= 50:
                            continue
                        if trend == 'SHORT' and rsi >= 50:
                            continue
                        
                        macd_phase, macd_value = self.calculate_macd_precise(closes_m15)
                        
                        if trend == 'LONG' and macd_phase != 'strong_bullish':
                            continue
                        if trend == 'SHORT' and macd_phase != 'strong_bearish':
                            continue
                        
                        signal_strength = abs(macd_value) * (rsi - 50 if trend == 'LONG' else 50 - rsi)
                        is_repeated = symbol.replace('/USDT', '') in prev_symbols
                        repeat_penalty = 0.5 if is_repeated else 1.0
                        
                        results.append({
                            'symbol': symbol.replace('/USDT', ''),
                            'trend': trend,
                            'signal': f"{trend} 🟢" if trend == 'LONG' else f"{trend} 🔴",
                            'price': last_price_m15,
                            'ema50': ema50_m15,
                            'rsi': round(rsi, 2),
                            'macd_phase': macd_phase,
                            'macd_value': round(macd_value, 4),
                            'diff_percent': round(((last_price_m15 - ema50_m15) / ema50_m15) * 100, 2),
                            'strength': signal_strength * repeat_penalty,
                            'is_repeated': is_repeated
                        })
                        
                    except Exception as e:
                        continue
                    
                    time.sleep(0.2)
                
                results.sort(key=lambda x: x['strength'], reverse=True)
                top_results = results[:10]
                
                new_symbols = [coin['symbol'] for coin in top_results]
                self.save_signals(new_symbols)
                
                self.progress.value = 100
                self.status_label.text = f"✅ اسکن کامل | {len(top_results)} سیگنال"
                
                if not top_results:
                    output = "❌ هیچ سیگنالی پیدا نشد!\n\n"
                    output += "🔍 دلایل:\n"
                    output += "• بازار در حالت رنج\n"
                    output += "• هیچ تغییری در MACD\n"
                    output += f"📊 {len(symbols)} ارز بررسی شد"
                else:
                    output = f"🎯 **۱۰ سیگنال برتر**\n"
                    output += f"📊 {len(symbols)} ارز بررسی شد\n"
                    output += "═" * 35 + "\n\n"
                    
                    for i, coin in enumerate(top_results, 1):
                        output += f"{i}. **{coin['symbol']}** {coin['signal']}\n"
                        output += f"   💰 قیمت: {coin['price']:,.2f} USDT\n"
                        output += f"   📈 RSI: {coin['rsi']}\n"
                        output += f"   📊 MACD: {'🟢 صعودی' if coin['macd_phase'] == 'strong_bullish' else '🔴 نزولی'}\n"
                        output += f"   📍 فاصله از EMA50: {coin['diff_percent']}%\n"
                        output += f"   ⚡ قدرت: {coin['strength']:.2f}\n"
                        if coin['is_repeated']:
                            output += f"   🔄 تکراری\n"
                        output += "\n" + "-" * 30 + "\n"
                
                self.result_label.text = output
                
            except Exception as e:
                self.result_label.text = f"❌ خطا:\n{str(e)}\n\nلطفاً VPN را روشن کنید"
                self.status_label.text = "❌ خطا"
        
        Clock.schedule_once(scan_async, 0.1)

if __name__ == '__main__':
    CryptoScannerApp().run()
