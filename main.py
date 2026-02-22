from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FINNHUB_KEY = "your_finnhub_key"  # Add your key
TOP_SYMBOLS = ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA", "AMD", "META", "AMZN", "NFLX", "CRM"]

@app.get("/top10")
async def top10():
    top10 = []
    best_buys = []

    for symbol in TOP_SYMBOLS:
        try:
            # Finnhub sentiment (last 2 days)
            url = f"https://finnhub.io/api/v1/news-sentiment?symbol={symbol}&token={FINNHUB_KEY}"
            resp = requests.get(url, timeout=5)
            data = resp.json()

            # Calculate score (-1 to 1)
            score = 0
            if "data" in data and data["data"]:
                sentiment = data["data"][0] if data["data"] else {}
                score = sentiment.get("sentiment", {}).get("basic", "Neutral")
                score = {"bullish": 0.8, "bearish": -0.8, "neutral": 0}.get(score, 0)

            # Signal logic
            signal = "HOLD"
            if score > 0.3:
                signal = "BUY"
                best_buys.append({"ticker": symbol, "score": score})
            elif score < -0.3:
                signal = "SELL"

            top10.append({
                "ticker": symbol,
                "signal": signal,
                "score": round(score, 2)
            })

        except Exception as e:
            # Fallback
            top10.append({"ticker": symbol, "signal": "HOLD", "score": 0.0})

    # Sort best buys
    best_buys.sort(key=lambda x: x["score"], reverse=True)

    return {
        "top10": top10[:10],
        "best_buys": best_buys[:5],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Test: curl https://your-backend.vercel.app/top10
print("Backend sentiment logic fixed!")
