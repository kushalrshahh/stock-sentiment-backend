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
    # Dynamic top volume (SPY/NASDAQ leaders)
    import yfinance as yf
    spy = yf.Ticker('^GSPC').history(period='2d')['Close']
    nasdaq = yf.Ticker('^IXIC').history(period='2d')['Close']
    # Top tickers from market leaders (or your watchlist fallback)
    active_tickers = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMD', 'MU', 'GOOGL', 'AMZN', 'META', 'NFLX']
    results = []
    for ticker in active_tickers:
        sent = await get_sentiment(ticker)
        results.append(sent)
    results.sort(key=lambda x: x['score'], reverse=True)
    return {'top10': results, 'best_buys': [r for r in results if r['signal']=='BUY'][:5], 'quick_sells': [r for r in results if r['signal']=='SELL'][:5]}
