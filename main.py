
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FlexSendMessage
import yfinance as yf
import json
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip().lower()
    if text.startswith('/'):
        symbol = text.replace('/stock', '').replace('/', '').upper()
        if not symbol:
            symbol = 'PLTR'
        message = get_stock_message(symbol)
        line_bot_api.reply_message(event.reply_token, message)

def get_stock_message(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    try:
        name = info.get('shortName', ticker)
        price = info['regularMarketPrice']
        change = info['regularMarketChange']
        change_percent = info['regularMarketChangePercent']
        volume = info.get('volume', 0)
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', '-')
        eps = info.get('trailingEps', '-')
        profit_margin = info.get('profitMargins', '-')

        flex_content = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": f"https://logo.clearbit.com/{info['website']}" if 'website' in info else "https://via.placeholder.com/1024x512.png?text=Stock",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": name, "weight": "bold", "size": "xl"},
                    {"type": "text", "text": f"ราคาล่าสุด: {price:.2f} USD", "size": "md", "color": "#555555"},
                    {"type": "text", "text": f"เปลี่ยนแปลง: {change:+.2f} ({change_percent:+.2f}%)", "size": "sm", "color": "#aaaaaa"},
                    {"type": "text", "text": f"Volume: {volume:,}", "size": "sm", "color": "#aaaaaa"},
                    {"type": "text", "text": f"Market Cap: {market_cap/1e9:.2f}B", "size": "sm", "color": "#aaaaaa"},
                    {"type": "text", "text": f"P/E: {pe_ratio}, EPS: {eps}", "size": "sm", "color": "#aaaaaa"},
                    {"type": "text", "text": f"Profit Margin: {profit_margin}", "size": "sm", "color": "#aaaaaa"},
                ]
            }
        }

        return FlexSendMessage(alt_text=f"{ticker} stock info", contents=flex_content)
    except Exception as e:
        return TextSendMessage(text=f"เกิดข้อผิดพลาดในการดึงข้อมูลหุ้น {ticker}\n{str(e)}")

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 8000))
app.run(host="0.0.0.0", port=port)

