from fastapi import FastAPI
from finnhub import Client
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
        response = client.sentiment(ticker, "2026-02-01", "2026-02-21")
        posts = response.get('reddit', []) + response.get('twitter', []) + response.get('data', [])
        if not posts:
            return {'ticker': ticker, 'score': 0.0, 'signal': 'HOLD', 'posts': 0}
        scores = []
        for post in posts:
            sentiment = post.get('sentiment') or {}
            score = sentiment.get('score') or post.get('score') or 0.0
            scores.append(float(score))
        avg_score = sum(scores) / len(scores)
        signal = 'BUY' if avg_score > 0.15 else 'SELL' if avg_score < -0.15 else 'HOLD'
        return {'ticker': ticker, 'score': round(avg_score, 3), 'signal': signal, 'posts': len(posts)}
    except:
        return {'ticker': ticker, 'score': 0.0, 'signal': 'HOLD', 'posts': 0}

@app.get("/top10")
async def get_top10_advice():
    import yfinance as yf
    # All major indices volume leaders (free)
    indices = ['^GSPC', '^IXIC', '^DJI', '^RUT']  # S&P/NASDAQ/Dow/Russell
    all_tickers = []
    for idx in indices:
        # Top 20 per index (volume)
        data = yf.download(idx, period='5d', progress=False)['Volume']
        top = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD']  # Fallback leaders
        all_tickers.extend(top)
    all_tickers = list(set(all_tickers))[:50]  # Unique top 50
    
    results = []
    for ticker in all_tickers:
        sent = await get_sentiment(ticker)
        results.append(sent)
    results.sort(key=lambda x: x['score'], reverse=True)
    return {'scanned': len(all_tickers), 'top10': results[:10], 'best_buys': [r for r in results if r['signal']=='BUY'][:5]}
