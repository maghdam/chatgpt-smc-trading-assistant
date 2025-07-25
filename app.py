# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel          # ←  put this line back
from typing import Optional, Literal
from notion_client import Client as NotionClient
from ctrader_client import (
    init_client,                       # still need this
    get_open_positions,
    get_ohlc_data,
    place_order,
    wait_for_deferred,
    symbol_name_to_id,
    client,
)
from twisted.internet import reactor
import threading
from ctrader_client import ACCOUNT_ID
import time


app = FastAPI()

# 🔌 ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def start_ctrader():
    """Spin up the cTrader Open API client once per worker."""
    if not reactor.running:                 # cheap guard
        threading.Thread(target=init_client, daemon=True).start()
# 🔌 ─────────────────────────────────────────────────────────────


# 🧠 Notion config
NOTION_SECRET = "your_notion_secret_key_here"
NOTION_DB_ID = "your_notion_database_id_here"
notion = NotionClient(auth=NOTION_SECRET)

# 📦 Data Request Schema
class FetchDataRequest(BaseModel):
    symbol: str
    timeframe: Optional[str] = "M5"
    num_bars: Optional[int] = 500
    return_chart: Optional[bool] = False

# 📓 Notion Journal Schema
class JournalEntry(BaseModel):
    title: str
    symbol: str
    session: str
    htf_bias: str
    entry_type: str
    entry_price: float
    stop_loss: float
    target_price: float
    order_type: str
    note: str = ""
    checklist: str = ""
    news_events: str = ""
    chart_url: str = ""

# 📤 Trade Execution Schema
class PlaceOrderRequest(BaseModel):
    symbol: str
    order_type: Literal["MARKET", "LIMIT", "STOP"]
    direction: Literal["BUY", "SELL"]
    volume: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

# ✅ Wait until symbols loaded
def wait_until_symbols_loaded(timeout=10):
    for _ in range(timeout * 10):
        if symbol_name_to_id:
            return True
        time.sleep(0.1)
    return False

@app.get("/health")
def health():
    return {
        "symbols_loaded": len(symbol_name_to_id),
        "connected": client.connected
    }

# 📟 Notion Entry Endpoint
@app.post("/journal-entry")
async def journal_entry(entry: JournalEntry):
    try:
        properties = {
            "Title": {"title": [{"text": {"content": entry.title}}]},
            "Symbol": {"rich_text": [{"text": {"content": entry.symbol}}]},
            "Session": {"rich_text": [{"text": {"content": entry.session}}]},
            "HTF Bias": {"rich_text": [{"text": {"content": entry.htf_bias}}]},
            "Entry Type": {"rich_text": [{"text": {"content": entry.entry_type}}]},
            "Entry Price": {"number": entry.entry_price},
            "Stop Loss": {"number": entry.stop_loss},
            "Target Price": {"number": entry.target_price},
            "Order Type": {"rich_text": [{"text": {"content": entry.order_type}}]},
            "Note": {"rich_text": [{"text": {"content": entry.note}}]},
            "Checklist": {"rich_text": [{"text": {"content": entry.checklist}}]},
            "News & Events": {"rich_text": [{"text": {"content": entry.news_events}}]},
        }

        if entry.chart_url:
            properties["Files & media"] = {"url": entry.chart_url}

        notion.pages.create(parent={"database_id": NOTION_DB_ID}, properties=properties)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📈 OHLC Data
@app.post("/fetch-data")
async def fetch_data(req: FetchDataRequest):
    try:
        symbol_key = req.symbol.upper()
        if symbol_key not in symbol_name_to_id:
            raise HTTPException(status_code=404, detail=f"Symbol '{req.symbol}' not found")

        if req.num_bars == 500:
            tf = req.timeframe.upper()
            req.num_bars = {
                "M1": 1500, "M5": 500, "M15": 500,
                "M30": 500, "H1": 500, "H4": 500,
                "D1": 300, "W1": 100
            }.get(tf, 500)

        data = get_ohlc_data(req.symbol, req.timeframe, req.num_bars)
        return {
            "symbol": req.symbol,
            "timeframe": req.timeframe,
            "ohlc": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📊 Open Positions
@app.get("/open-positions")
async def open_positions():
    try:
        positions = get_open_positions()
        return {"positions": positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🎯 Execute Trade Order
@app.post("/place-order")
def execute_trade(order: PlaceOrderRequest):
    try:
        if not wait_until_symbols_loaded():
            raise HTTPException(status_code=503, detail="Symbols not loaded yet. Try again shortly.")

        symbol_key = order.symbol.upper()
        if symbol_key not in symbol_name_to_id:
            raise HTTPException(status_code=404, detail=f"Symbol '{order.symbol}' not found.")

        symbol_id = symbol_name_to_id[symbol_key]

        print(f"[ORDER DEBUG] Sending order: {order=}, {symbol_id=}")
        deferred = place_order(
            client=client,
            account_id=ACCOUNT_ID,
            symbol_id=symbol_id,
            order_type=order.order_type,
            side=order.direction,
            volume=order.volume,
            price=order.entry_price,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit
        )

        result = wait_for_deferred(deferred, timeout=10)

        if isinstance(result, str):
            result = {"message": result}
        elif not isinstance(result, dict):
            result = {"result": str(result)}

        return {
            "status": "success",
            "submitted": True,
            "details": result
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def stop_ctrader():
    if reactor.running:
        reactor.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

