from fastapi import FastAPI
from finnhub import Client
import yfinance as yf
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
client = Client(api_key=os.getenv("FINNHUB_API_KEY"))

@app.get("/")
async def root():
    return {"message": "Sentiment API Ready"}

@app.get("/sentiment/{ticker}")
async def get_sentiment(ticker: str):
    try:
        data = client.sentiment(ticker, "2026-02-20", "2026-02-21")  # Yesterday-today
        if not data['data']: return {"error": "No sentiment data"}
        scores = [s['sentiment']['score'] for s in data['data']]
        avg_score = sum(scores) / len(scores)
        signal = 'BUY' if avg_score > 0.15 else 'SELL' if avg_score < -0.15 else 'HOLD'
        return {'ticker': ticker, 'score': round(avg_score, 3), 'signal': signal, 'posts': len(data['data'])}
    except Exception as e:
        return {"error": str(e)}

@app.get("/top10")
async def get_top10_advice():
    active_tickers = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMD', 'MU', 'GOOGL', 'BAC', 'AMZN', 'META']  # Top daily vol[web:54]
    results = []
    for ticker in active_tickers:
        sent = await get_sentiment(ticker)
        if 'error' not in sent:
            results.append(sent)
    results.sort(key=lambda x: x['score'], reverse=True)
    buys = [r for r in results if r['signal']=='BUY'][:5]
    sells = [r for r in results if r['signal']=='SELL'][:3]
    return {'top10': results[:10], 'best_buys': buys, 'quick_sells': sells}
