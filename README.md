# 📊 ChatGPT Trading Strategy Assistant with cTrader API

A fully automated and extensible trading assistant powered by ChatGPT — capable of analyzing, journaling, and executing trades in Forex, indices, and stocks using natural language.

This framework integrates the **cTrader Open API**, a **FastAPI backend**, and **Docker**, delivering a seamless end-to-end trading pipeline — from market analysis to order placement — all controlled through conversation.

🧠 **Currently configured to run a Smart Money Concepts (SMC)** strategy out of the box.  
🛠️ You can easily adapt it to **any strategy** by modifying the ChatGPT instructions.

---

## 🔑 Key Features

- **Strategy-Agnostic Design**  
  Define your own rules — just update the ChatGPT prompt instructions, and the assistant adapts accordingly.

- **Advanced SMC Market Analysis**  
  Detects CHOCH, BOS, FVGs, OBs, liquidity sweeps, and premium/discount zones.

- **Trade Journaling**  
  Automatically logs trades to Notion with structured metadata, SMC checklists, and chart snapshots.

- **Order Execution**  
  Places market, limit, and stop orders in real time using plain English.

- **Multilingual Support**  
  Works in English, French, Spanish, and any language ChatGPT understands.

- **Live Market Sync**  
  Fetches price data and executes logic live through the cTrader Open API.



---

## 🧩 Project Structure

```bash
chatgpt-smc-trading-assistant/
├── app.py                  # FastAPI backend
├── ctrader_client.py       # Twisted client for cTrader Open API
├── Dockerfile              # Build config for backend container
├── docker-compose.yml      # Launches backend + ngrok
├── requirements.txt        # Python dependencies
├── .env                    # API credentials (not committed) - see .env.example
├── gpt_instructions.md     # GPT instruction template
├── gpt-schema.yaml         # GPT Action schema (OpenAPI YAML)
├── docker_usage_guide.md   # Step-by-step guide for using Docker and Docker Compose with the project
└── README.md               # Project overview and usage
```

### 📌 Strategy Customization – Create Your Own Logic

This assistant is **strategy-agnostic** — you're not limited to Smart Money Concepts (SMC).

You can define and run **any trading strategy** simply by rewriting the prompt instructions.

#### ✍️ How to Create a New Strategy

1. Open **ChatGPT → My GPTs**
2. Select your GPT (e.g., `SMC Swing Trading cTrader`)
3. Click **Edit GPT → Configure**
4. In the **Instructions** field:
   - Replace the existing SMC prompt with your own strategy guide
   - Describe how the GPT should analyze OHLC and chart image inputs
   - Specify what to detect (e.g., trend direction, breakout signals, RSI divergence, etc.)
   - Define entry/exit rules (market/pending orders, SL/TP logic, filters)

> 💡 **Example**:  
> “Use Fibonacci retracement zones (0.5–0.618) combined with bullish MACD crossovers to identify long entries. Confirm structure with higher-timeframe trend direction. Return: signal, SL, TP, and confidence.”

Once saved, the GPT will analyze live data from cTrader and generate trading decisions **based on your strategy logic** — no additional code needed.


---

## 🧠 Project Overview

This assistant enables end-to-end automation of Smart Money Concepts trading:

### 🔹 Backend (Python + FastAPI)

- Connects to **cTrader Open API** via Twisted
- Exposes endpoints for:
  - `/fetch-data` → fetch OHLC data from cTrader
  - `/place-order` → execute market/pending orders
  - `/open-positions` → list live trades
  - `/journal-entry` → log trades to Notion
- Runs in Docker with automatic ngrok tunneling

### 🔸 Frontend (ChatGPT Custom GPT)

- Built inside **ChatGPT Plus** under “My GPTs”
- Automatically calls backend endpoints for:
  - 🔍 SMC trade analysis: CHOCH, FVG, OBs, liquidity, etc.
  - 📰 Macro event checking from Investing.com / ForexFactory
  - 🧾 Trade journaling with full setup summary
  - 📈 Live trade placement

---

## 🛠️ Setup Instructions

### ✅ Requirements
- Python 3.10 or newer
- Docker and Docker Compose
- Cloud for deploying FastAPI backend like Render (or Fly.io)
- Demo cTrader broker account (such as IC Markets or Pepperstone)
- OpenApi account: https://connect.spotware.com/apps
- OpenAI ChatGPT Plus subscription
- Notion account with integration enabled: https://www.notion.so/profile/integrations


### 🌐 Deployment and Integration

#### 🧠 1. Deploy Backend on Render (or Fly.io)

Render makes it easy to deploy your FastAPI backend:
- Push code to GitHub
- Connect repo to Render
- Set environment variables manually (from your local .env)
- Get a permanent public URL (e.g. https://your-service.onrender.com)


#### 🤩 2. Connect Backend to ChatGPT
- Inside ChatGPT Plus:
- Go to Explore GPTs → Create → Configure
- In Instructions, paste your trading logic (e.g., SMC)
- In Actions, paste your gpt-schema.yaml
- Under API Base URL, enter your Render public URL (e.g., https://your-service.onrender.com)

Done! You can now ask questions like:
  "Analyze EURUSD using SMC and journal the trade"


### 📦 Local Development (Optional)

1. **Clone the repo**

```bash
git clone https://github.com/yourusername/chatgpt-smc-trading-assistant.git
cd chatgpt-smc-trading-assistant
```

2. **Edit** with your:

   - cTrader clientId, accessToken, accountId
   - ngrok authtoken

3. **Run with Docker Compose**

```bash
docker-compose up --build
```

But we recommend deploying it to the cloud for uninterrupted GPT access or ngrok to link the api to chatgpt.

---

## 🖼️ Screenshots

### 🧠 GPT Assistant (Frontend UI)
This is the interface of the custom GPT created for Smart Money Concepts trading analysis.

![ GPT Assistant ](images/gpt-frontend.png)

### 🔍 GPT Setup  (Instructions + Action Schema)

GPT Instruction Configuration
![GPT Setup](images/gpt-configuration-instruction.png)

GPT Action Schema Integration
![GPT Setup](images/gpt-configuration-action-schema.png)



## Example Natural Language Queries

- Scan my 6-symbol list — EURUSD, NAS100, XAUUSD, GBPUSD, US30, BTCUSD — and give me the top 2–3 instruments showing the best SMC setups for today. Focus on clean structure, HTF alignment, and actionable intraday zones.
- Analyze EURUSD for a swing trade setup
- Reevaluate my EURUSD open position
- Is my EURUSD trade still valid?
- Should I move SL to breakeven on EURUSD?
- Are there any major news events today?
- What’s the macro outlook for EUR/USD this week?
- Update me on any SMC confluence for EURUSD 
- Return all opened positions
- Return all pending oders



## Example Outputs

### EURUSD: Smart Money Concepts (SMC) Analysis

---

### 🔷 HTF Bias: Bullish

* **D1** has been consistently printing higher highs and higher lows from mid-June.
* Recent pullback respected prior demand zone (around 1.159–1.162), suggesting continuation potential.

### 🔶 MTF Zones (H4)

* **Bullish structure remains intact**, with a recent pullback into demand near 1.17400.
* There’s a **retest of a bullish OB** (H4 demand from 1.1730–1.1755).
* Multiple rejections from the 1.1730s confirming strong demand.

### 🟢 LTF Entry (M15): Confirmed

* LTF shows **liquidity sweep** below intra-session low at 1.1737, followed by strong bullish candles.
* Price reclaimed 1.1750 level with a potential **FVG entry** around 1.1744–1.1748.
* Clean upside candle structure with minor pullbacks — suggesting building momentum.

---

### ✅ SMC Checklist

* **CHOCH**: ✅ (M15 bullish CHOCH above 1.1755)
* **OB**: ✅ (H4 demand OB 1.1730–1.1755)
* **FVG**: ✅ (M15 FVG 1.1744–1.1748)
* **Sweep**: ✅ (LTF swept liquidity under 1.1737)
* **Candle Confirmations**: ✅ (Bullish engulfing and follow-through on M15)

---

### 📓 News & Events

* No high-impact USD or EUR events within the current 24h window (checked via Investing.com)
* Next notable USD macro event is tomorrow: **US Core PCE release**

---

### 🧠 Final Tip

* This setup offers a strong long opportunity with confluence from HTF to LTF.
* A tight SL below the sweep (1.1730) and target near HTF resistance (1.1825) gives a good R\:R.

---

### 📟 Suggested Trade Journal Entry

| Field            | Value                                         |
| ---------------- | --------------------------------------------- |
| **Title**        | 2025-07-25 EURUSD NY                          |
| **Symbol**       | EURUSD                                        |
| **Session**      | NY                                            |
| **HTF Bias**     | Bullish                                       |
| **Entry Type**   | FVG Retest + OB                               |
| **Entry Price**  | 1.17460                                       |
| **Stop Loss**    | 1.17280                                       |
| **Target Price** | 1.18250                                       |
| **Order Type**   | Buy Limit                                     |
| **Note**         | LTF liquidity sweep + FVG fill inside H4 OB   |
| **Checklist**    | CHOCH ✅, OB ✅, FVG ✅, Sweep ✅, Candle Conf. ✅ |
| **News Events**  | US Core PCE release tomorrow (USD)            |



Would you like a visual SMC chart for this setup?


### 🧠 Trade Analysis Output
Live OHLC analysis, SMC element detection, and structured journal suggestion.

![ChatGPT Trade Analysis](images/trade-analysis.png)

Would you like me to journal this or place the trade?

### 📈 Order Execution via cTrader
Automatically places pending or market orders via the FastAPI backend.

![Order Execution](images/order-execution.png)
 

### 📓 Notion Journal Entry
Posts the confirmed trades, with checklist, news context, and chart links into Notion.

![Notion Entry](images/notion-journal.png)



---

## ⚠️ Disclaimer

> This project is intended for **educational and learning purposes only**. Do **not** use it for real trading with live money. Always test with **demo accounts** as shown in the examples. Trading involves significant risk.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
