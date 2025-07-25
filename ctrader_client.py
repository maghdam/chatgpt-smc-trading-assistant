
# ctrader_client.py
# ---------------------------------------------------------------------------

from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
    ProtoOASymbolsListReq,
    ProtoOAReconcileReq,
    ProtoOAGetTrendbarsReq,
    ProtoOANewOrderReq,
    ProtoOAAmendOrderReq,
    ProtoOAAmendPositionSLTPReq,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
    ProtoOAOrderType,
    ProtoOATradeSide,
    ProtoOATrendbarPeriod,
)
from twisted.internet import reactor
from datetime import datetime, timezone, timedelta
import calendar, time, threading, json

# ── credentials & client ───────────────────────────────────────────────────
with open("credentials.json") as f:
    creds = json.load(f)

CLIENT_ID     = creds["ClientId"]
CLIENT_SECRET = creds["Secret"]
ACCOUNT_ID    = creds["AccountId"]
ACCESS_TOKEN  = creds["AccessToken"]

host   = EndPoints.PROTOBUF_LIVE_HOST if creds["HostType"].lower() == "live" else EndPoints.PROTOBUF_DEMO_HOST
client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)

# ── symbol maps ────────────────────────────────────────────────────────────
symbol_map        : dict[int, str] = {}   # {id: name}
symbol_name_to_id : dict[str, int] = {}   # {name.upper(): id}
symbol_digits_map : dict[int, int] = {}   # {id: digits}

# ── helpers ────────────────────────────────────────────────────────────────
def pips_to_relative(pips: int, digits: int) -> int:
    """Convert pips → 1/100 000 of price units (works for 2- to 5-digit symbols)."""
    return pips * 10 ** (6 - digits)

def on_error(failure):  # generic errback
    print("[ERROR]", failure)

# ── auth & symbol bootstrap ────────────────────────────────────────────────
def symbols_response_cb(res):
    global symbol_map, symbol_name_to_id, symbol_digits_map
    symbol_map.clear(); symbol_name_to_id.clear(); symbol_digits_map.clear()

    symbols = Protobuf.extract(res)
    for s in symbols.symbol:
        # → try `digits`, fall back to `pipPosition`, default = 5
        digits = getattr(s, "digits", getattr(s, "pipPosition", 5))

        symbol_map[s.symbolId]            = s.symbolName
        symbol_name_to_id[s.symbolName.upper()] = s.symbolId
        symbol_digits_map[s.symbolId]     = digits

    print(f"[DEBUG] Loaded {len(symbol_map)} symbols.")


# ── account‑level auth → ask for symbol list ─────────────────────────────
def account_auth_cb(_):
    req = ProtoOASymbolsListReq(
        ctidTraderAccountId=ACCOUNT_ID,
        includeArchivedSymbols=False,
    )
    # when the symbols arrive we’ll call symbols_response_cb
    client.send(req).addCallbacks(symbols_response_cb, on_error)


def app_auth_cb(_):
    req = ProtoOAAccountAuthReq(
        ctidTraderAccountId=ACCOUNT_ID,
        accessToken=ACCESS_TOKEN,
    )
    # account_auth_cb must exist in the same module
    client.send(req).addCallbacks(account_auth_cb, on_error)


def connected(_):
    req = ProtoOAApplicationAuthReq(clientId=CLIENT_ID, clientSecret=CLIENT_SECRET)
    client.send(req).addCallbacks(app_auth_cb, on_error)

def init_client():
    client.setConnectedCallback(connected)
    client.setDisconnectedCallback(lambda c, r: print("[INFO] Disconnected:", r))
    client.setMessageReceivedCallback(lambda c, m: None)
    client.startService()
    reactor.run(installSignalHandlers=False)


# ── OHLC fetch (used by /fetch-data) ───────────────────────────────────────
daily_bars, ready_event = [], threading.Event()

def _trendbars_cb(res):
    bars = Protobuf.extract(res).trendbar
    def _tb(tb):
        ts = datetime.fromtimestamp(tb.utcTimestampInMinutes * 60, timezone.utc)
        return dict(
            time   = ts.isoformat(),
            open   = (tb.low + tb.deltaOpen)   / 100_000,
            high   = (tb.low + tb.deltaHigh)   / 100_000,
            low    = tb.low                    / 100_000,
            close  = (tb.low + tb.deltaClose)  / 100_000,
            volume = tb.volume,
        )
    global daily_bars
    daily_bars = list(map(_tb, bars))[-50:]
    ready_event.set()

def get_ohlc_data(symbol: str, tf: str = "D1", n: int = 10):
    ready_event.clear()
    sid = symbol_name_to_id.get(symbol.upper())
    if sid is None:
        raise ValueError(f"Unknown symbol '{symbol}'")

    now = datetime.utcnow()
    req = ProtoOAGetTrendbarsReq(
        symbolId            = sid,
        ctidTraderAccountId = ACCOUNT_ID,
        period              = getattr(ProtoOATrendbarPeriod, tf),
        fromTimestamp       = int(calendar.timegm((now - timedelta(weeks=52)).utctimetuple())) * 1000,
        toTimestamp         = int(calendar.timegm(now.utctimetuple())) * 1000,
    )
    client.send(req).addCallbacks(_trendbars_cb, on_error)
    ready_event.wait(10)
    return daily_bars[-n:]

# ── reconcile helpers ──────────────────────────────────────────────────────
open_positions, pos_ready = [], threading.Event()

def _reconcile_cb(res):
    global open_positions
    open_positions = []
    rec = Protobuf.extract(res)
    for p in rec.position:
        td = p.tradeData
        open_positions.append(
            dict(
                symbol_name = symbol_map.get(td.symbolId, str(td.symbolId)),
                position_id = p.positionId,
                direction   = "buy" if td.tradeSide == ProtoOATradeSide.BUY else "sell",
                entry_price = getattr(p, "price", 0),  # already a float like 1.17700
                volume_lots = td.volume / 10_000_000,  # 1 lot = 10 000 000
            )
        )
    pos_ready.set()

def get_open_positions():
    pos_ready.clear()
    req = ProtoOAReconcileReq(ctidTraderAccountId = ACCOUNT_ID)
    client.send(req).addCallbacks(_reconcile_cb, on_error)
    pos_ready.wait(5)
    return open_positions

# ── core: place_order ──────────────────────────────────────────────────────
# ── core: place_order ──────────────────────────────────────────────────────
def place_order(
    *, client, account_id, symbol_id,
    order_type, side, volume,
    price=None, stop_loss=None, take_profit=None,
    client_msg_id=None,
):
    # 1 lot  →  10 000 000 units   (✅ correct scale)
    req = ProtoOANewOrderReq(
        ctidTraderAccountId=account_id,
        symbolId=symbol_id,
        orderType=ProtoOAOrderType.Value(order_type.upper()),
        tradeSide=ProtoOATradeSide.Value(side.upper()),
        volume=int(volume * 10_000_000),
    )

    # -------- absolute price fields are now plain floats ------------------
    if order_type.upper() == "LIMIT":
        if price is None:
            raise ValueError("Limit order requires price.")
        req.limitPrice = float(price)          # e.g. 1.17700
    elif order_type.upper() == "STOP":
        if price is None:
            raise ValueError("Stop order requires price.")
        req.stopPrice = float(price)

    if order_type.upper() in ("LIMIT", "STOP"):
        if stop_loss   is not None:
            req.stopLoss   = float(stop_loss)
        if take_profit is not None:
            req.takeProfit = float(take_profit)
    # ---------------------------------------------------------------------

    # MARKET orders → relative distances (still 1 / 100 000 units)
    else:
        digits = symbol_digits_map.get(symbol_id, 5)
        if stop_loss is not None:
            req.relativeStopLoss   = pips_to_relative(int(stop_loss),   digits)
        if take_profit is not None:
            req.relativeTakeProfit = pips_to_relative(int(take_profit), digits)

    print(
        f"[DEBUG] Sending order: {order_type=} {side=} "
        f"price={price} SL={stop_loss} TP={take_profit}"
    )
    d = client.send(req, client_msg_id=client_msg_id)

    # legacy patch after MARKET fill (unchanged)
    if order_type.upper() == "MARKET" and isinstance(stop_loss, float) and stop_loss > 1:
        def _after_fill(_):
            time.sleep(2)
            for p in get_open_positions():
                if (
                    p["symbol_name"].upper() == symbol_map[symbol_id].upper()
                    and p["direction"].upper() == side.upper()
                ):
                    return modify_position_sltp(
                        client=client,
                        account_id=account_id,
                        position_id=p["position_id"],
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                    )
            return {"status": "position_not_found"}
        d.addCallback(_after_fill)

    return d



# ── amend helpers (rarely needed with new logic) ───────────────────────────
def modify_position_sltp(client, account_id, position_id, stop_loss=None, take_profit=None):
    req = ProtoOAAmendPositionSLTPReq(ctidTraderAccountId = account_id, positionId = position_id)
    if stop_loss   is not None: req.stopLoss   = stop_loss
    if take_profit is not None: req.takeProfit = take_profit
    return client.send(req)

def modify_pending_order_sltp(client, account_id, order_id, version, stop_loss=None, take_profit=None):
    req = ProtoOAAmendOrderReq(
        ctidTraderAccountId = account_id,
        orderId             = order_id,
        version             = version,
    )
    if stop_loss   is not None: req.stopLoss   = stop_loss
    if take_profit is not None: req.takeProfit = take_profit
    return client.send(req)

# ── blocking helper used by FastAPI layer ─────────────────────────────────
def wait_for_deferred(d, timeout=10):
    evt, box = threading.Event(), {}
    d.addCallbacks(lambda r: (box.setdefault("r", r), evt.set()), lambda f: (box.setdefault("f", f), evt.set()))
    evt.wait(timeout)
    return box.get("r") or {"status": "failed", "error": str(box.get("f"))}

def get_pending_orders():
    request = ProtoOAReconcileReq()
    request.ctidTraderAccountId = ACCOUNT_ID

    result_ready = threading.Event()
    orders = []

    def callback(response):
        res = Protobuf.extract(response)
        orders.extend(res.order)  # only pending orders
        result_ready.set()

    d = client.send(request)
    d.addCallbacks(callback, on_error)
    result_ready.wait(timeout=5)

    return orders

