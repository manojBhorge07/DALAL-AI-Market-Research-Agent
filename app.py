import json, os, re, time, random
from datetime import datetime
import pytz
import streamlit as st
import anthropic

st.set_page_config(page_title="DALAL AI Agent", page_icon="📈", layout="wide")

# -----------------------------
# DATA / CONFIG
# -----------------------------
STOCKS = {
    "RELIANCE": {"price":2945.40,"pe":24.8,"sector":"Energy / Telecom","mktcap":"₹19.94L Cr","hi52":3024.90,"lo52":2220.30},
    "TCS": {"price":3820.75,"pe":32.4,"sector":"IT Services","mktcap":"₹13.86L Cr","hi52":4255.00,"lo52":3311.75},
    "HDFCBANK": {"price":1642.30,"pe":19.2,"sector":"Banking","mktcap":"₹12.48L Cr","hi52":1794.00,"lo52":1363.55},
    "INFY": {"price":1498.20,"pe":27.1,"sector":"IT Services","mktcap":"₹6.24L Cr","hi52":1903.00,"lo52":1355.75},
    "ICICIBANK": {"price":1082.45,"pe":17.8,"sector":"Banking","mktcap":"₹7.62L Cr","hi52":1196.90,"lo52":899.00},
    "WIPRO": {"price":480.15,"pe":21.6,"sector":"IT Services","mktcap":"₹2.51L Cr","hi52":566.80,"lo52":371.00},
    "BAJFINANCE": {"price":6820.80,"pe":30.2,"sector":"NBFC","mktcap":"₹4.11L Cr","hi52":8192.00,"lo52":6220.00},
    "TATAMOTORS": {"price":942.55,"pe":9.4,"sector":"Auto","mktcap":"₹3.47L Cr","hi52":1179.00,"lo52":652.20},
    "SUNPHARMA": {"price":1534.90,"pe":34.7,"sector":"Pharma","mktcap":"₹3.68L Cr","hi52":1960.00,"lo52":1080.00},
    "ADANIENT": {"price":2840.10,"pe":88.2,"sector":"Conglomerate","mktcap":"₹3.24L Cr","hi52":3743.00,"lo52":1017.05},
    "MARUTI": {"price":11240.30,"pe":26.8,"sector":"Auto","mktcap":"₹3.40L Cr","hi52":13680.00,"lo52":9613.40},
    "SBIN": {"price":742.80,"pe":9.8,"sector":"PSU Banking","mktcap":"₹6.63L Cr","hi52":912.00,"lo52":543.20},
    "ONGC": {"price":272.40,"pe":7.2,"sector":"Oil & Gas","mktcap":"₹3.43L Cr","hi52":345.00,"lo52":164.55},
    "LT": {"price":3480.60,"pe":36.2,"sector":"Infrastructure","mktcap":"₹4.79L Cr","hi52":3849.90,"lo52":2472.50},
    "AXISBANK": {"price":1064.20,"pe":14.6,"sector":"Banking","mktcap":"₹3.28L Cr","hi52":1339.65,"lo52":885.00},
    "BHARTIARTL": {"price":1542.30,"pe":82.4,"sector":"Telecom","mktcap":"₹9.20L Cr","hi52":1779.00,"lo52":1020.40},
    "KOTAKBANK": {"price":1782.40,"pe":22.8,"sector":"Banking","mktcap":"₹3.55L Cr","hi52":1942.00,"lo52":1544.00},
    "NTPC": {"price":362.15,"pe":18.4,"sector":"Power","mktcap":"₹3.51L Cr","hi52":448.45,"lo52":222.90},
    "POWERGRID": {"price":310.40,"pe":19.6,"sector":"Power","mktcap":"₹2.89L Cr","hi52":366.25,"lo52":211.00},
}

def get_stock(symbol):
    symbol = symbol.upper().strip()
    if symbol in STOCKS:
        return STOCKS[symbol]
    return {"price": round(random.uniform(200,3000),2), "pe": None, "sector":"Unknown",
            "mktcap":"N/A","hi52":None,"lo52":None}

def now_ist():
    return datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S")

# -----------------------------
# AGENT ENGINE
# -----------------------------
class DalalAgent:
    """A small multi-agent trading-analysis framework.

    Agents:
      1. Orchestrator - coordinates workflow
      2. Analyst - produces market analysis
      3. Risk Manager - determines position/risk parameters
      4. Executor - prepares an order but NEVER sends it to a broker
    """

    def __init__(self, api_key=None):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def _claude_json(self, prompt, max_tokens=700):
        response = self.client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=max_tokens,
            messages=[{"role":"user","content":prompt}],
        )
        text = response.content[0].text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("Model did not return JSON")
        return json.loads(match.group(0))

    def analyst(self, symbol, exchange, strategy, market):
        prompt = f"""
You are the ANALYST agent in a paper-trading research system.
Analyze {exchange}:{symbol} using the {strategy} strategy.

Known market snapshot:
CMP: ₹{market['price']}
P/E: {market.get('pe')}
Sector: {market['sector']}
Market cap: {market['mktcap']}
52W high: ₹{market.get('hi52')}
52W low: ₹{market.get('lo52')}

This is NOT live market data. Do not invent live FII/DII flows, news, prices, indicators,
or regulatory facts. Treat missing data as unknown.

Return ONLY JSON:
{{
  "signal": "BUY|SELL|HOLD",
  "confidence": 0,
  "priceTarget": 0,
  "keyFactors": ["...","...","..."],
  "support": 0,
  "resistance": 0,
  "indiaContext": "...",
  "summary": "..."
}}
"""
        return self._claude_json(prompt, 800)

    def risk_manager(self, symbol, risk_level, analyst, market):
        portfolio = 842680.0
        cash = 218400.0
        risk_pct = {"Conservative":0.03, "Moderate":0.05, "Aggressive":0.08}[risk_level]
        price = float(market["price"])
        max_position = min(portfolio * risk_pct, cash)
        shares = max(1, int(max_position / price))
        stop = round(price * 0.96, 2)
        target = round(price * 1.10, 2)
        max_loss = round(max(0, price-stop) * shares, 2)
        position_value = round(price * shares, 2)

        # Risk sizing is deterministic rather than asking an LLM to invent account constraints.
        return {
            "shares": shares,
            "stopLoss": stop,
            "takeProfit": target,
            "rrRatio": "1:2.5",
            "riskScore": min(100, round((max_loss / portfolio) * 100 * 8)),
            "maxLoss": max_loss,
            "positionValue": position_value,
            "notes": f"{risk_level} sizing: max position ₹{max_position:,.0f}; cash capped.",
        }

    def execute_preview(self, decision):
        return {
            "status": "AWAITING_CONFIRMATION",
            "order_type": "PAPER_LIMIT",
            "symbol": decision["symbol"],
            "exchange": decision["exchange"],
            "side": decision["signal"],
            "quantity": decision["shares"],
            "price": decision["entry"],
            "stop_loss": decision["stopLoss"],
            "take_profit": decision["takeProfit"],
        }

    def run(self, symbol, exchange, strategy, risk_level):
        market = get_stock(symbol)
        logs = []
        logs.append(("ORCH", f"Starting pipeline {exchange}:{symbol} / {strategy} / {risk_level}"))
        logs.append(("ORCH", f"Market snapshot ₹{market['price']} | {market['sector']}"))
        logs.append(("ANALYST", "Analyzing market snapshot..."))

        if self.client:
            try:
                analyst = self.analyst(symbol, exchange, strategy, market)
                logs.append(("ANALYST", "Claude analysis completed."))
            except Exception as exc:
                logs.append(("ANALYST", f"Claude unavailable: {str(exc)[:80]}"))
                analyst = self.fallback_analyst(strategy, market)
        else:
            analyst = self.fallback_analyst(strategy, market)
            logs.append(("ANALYST", "No API key: using deterministic demo analysis."))

        logs.extend(("ANALYST", f"→ {x}") for x in analyst.get("keyFactors", []))
        logs.append(("RISK", "Calculating deterministic risk limits..."))
        risk = self.risk_manager(symbol, risk_level, analyst, market)
        logs.append(("RISK", risk["notes"]))
        logs.append(("ORCH", "Synthesizing analyst + risk output."))

        decision = {
            "symbol": symbol.upper(), "exchange": exchange, "sector": market["sector"],
            "strategy": strategy, "signal": analyst["signal"],
            "confidence": int(analyst["confidence"]), "summary": analyst.get("summary",""),
            "entry": market["price"], "stopLoss": risk["stopLoss"],
            "takeProfit": risk["takeProfit"], "shares": risk["shares"],
            "rrRatio": risk["rrRatio"], "riskScore": risk["riskScore"],
            "maxLoss": risk["maxLoss"], "positionValue": risk["positionValue"],
            "keyFactors": analyst.get("keyFactors", []),
            "indiaContext": analyst.get("indiaContext", ""),
        }
        order = self.execute_preview(decision)
        logs.append(("EXEC", "Order prepared as PAPER order. No broker API is connected."))
        return decision, order, logs

    @staticmethod
    def fallback_analyst(strategy, market):
        price = market["price"]
        # Transparent demo heuristic: no claim that this is a live signal.
        if market.get("pe") is not None and market["pe"] < 15:
            signal = "BUY"
        elif market.get("pe") is not None and market["pe"] > 70:
            signal = "HOLD"
        else:
            signal = "HOLD"
        return {
            "signal": signal, "confidence": 55,
            "priceTarget": round(price * 1.08, 2),
            "keyFactors": [
                "Demo mode: using supplied stock snapshot",
                f"P/E input: {market.get('pe', 'unknown')}",
                f"Strategy selected: {strategy}",
            ],
            "support": round(price*0.95,2),
            "resistance": round(price*1.07,2),
            "indiaContext": "Live India-specific context is unavailable in demo mode.",
            "summary": f"Demo {signal} assessment; connect Claude and live data sources for deeper research.",
        }

# -----------------------------
# UI
# -----------------------------
st.markdown("""
<style>
body, .stApp {background:#050912;}
.block-container {max-width:1400px;padding-top:1.2rem;}
.card {background:#0b1320;border:1px solid #20324a;border-radius:10px;padding:16px;margin-bottom:12px;}
.logo {font-size:32px;font-weight:900;letter-spacing:7px;}
.sub {color:#7190a8;font-size:11px;letter-spacing:3px;}
.buy {color:#00d084;font-weight:800;}
.sell {color:#ff5364;font-weight:800;}
.hold {color:#ffd43b;font-weight:800;}
.small {font-size:12px;color:#7190a8;}
</style>
""", unsafe_allow_html=True)

if "decision" not in st.session_state: st.session_state.decision = None
if "logs" not in st.session_state: st.session_state.logs = []
if "paper_orders" not in st.session_state: st.session_state.paper_orders = []

st.markdown('<div class="card"><div class="logo">DALAL</div><div class="sub">MULTI-AGENT INDIAN MARKET RESEARCH + PAPER TRADING</div></div>', unsafe_allow_html=True)

left, main, right = st.columns([1.05, 2.2, 1.05])

with left:
    st.markdown("### Agents")
    for name, role in [
        ("ORCHESTRATOR","Workflow coordinator"),
        ("ANALYST","Market research"),
        ("RISK MGR","Deterministic sizing"),
        ("EXECUTOR","Paper-order preview"),
    ]:
        st.markdown(f'<div class="card"><b>{name}</b><br><span class="small">{role}</span></div>', unsafe_allow_html=True)

    st.markdown("### Demo portfolio")
    st.metric("Portfolio", "₹8,42,680")
    st.metric("Cash", "₹2,18,400")
    st.caption("Demo values only.")

with main:
    st.markdown("### Analysis Command")
    symbol = st.text_input("Stock symbol", "RELIANCE").upper().strip()
    exchange = st.selectbox("Exchange", ["NSE","BSE"])
    strategy = st.selectbox("Strategy", ["Momentum","Mean Reversion","Breakout","Swing Trade","Positional"])
    risk = st.selectbox("Risk level", ["Conservative","Moderate","Aggressive"], index=1)
    api_key = st.text_input("Anthropic API key (optional)", type="password",
                            help="Used only for this session. Put ANTHROPIC_API_KEY in .env for a local setup if preferred.")

    if st.button("▶ RUN AGENT PIPELINE", use_container_width=True):
        with st.spinner("Agents working..."):
            agent = DalalAgent(api_key or os.getenv("ANTHROPIC_API_KEY"))
            decision, order, logs = agent.run(symbol, exchange, strategy, risk)
            st.session_state.decision = decision
            st.session_state.logs = logs

    if st.session_state.logs:
        st.markdown("### Agent Log")
        st.code("\n".join(f"[{a}] {m}" for a,m in st.session_state.logs), language="text")

    d = st.session_state.decision
    if d:
        cls = d["signal"].lower()
        st.markdown(f"""
        <div class="card">
          <div class="small">AGENT DECISION</div>
          <h1 class="{cls}">{d['signal']}</h1>
          <p>{d['summary']}</p>
          <p><b>Confidence:</b> {d['confidence']}% &nbsp; | &nbsp;
             <b>Entry:</b> ₹{d['entry']:,.2f} &nbsp; | &nbsp;
             <b>Quantity:</b> {d['shares']}</p>
          <p><b>Stop:</b> ₹{d['stopLoss']:,.2f} &nbsp; | &nbsp;
             <b>Target:</b> ₹{d['takeProfit']:,.2f} &nbsp; | &nbsp;
             <b>R:R:</b> {d['rrRatio']}</p>
          <p><b>Position:</b> ₹{d['positionValue']:,.2f} &nbsp; | &nbsp;
             <b>Max loss:</b> ₹{d['maxLoss']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Key factors**")
        for factor in d["keyFactors"]:
            st.write("•", factor)
        if d["indiaContext"]:
            st.info(d["indiaContext"])

        if d["signal"] != "HOLD":
            if st.button("✓ CONFIRM PAPER ORDER", use_container_width=True):
                preview = DalalAgent().execute_preview(d)
                st.session_state.paper_orders.insert(0, {
                    **preview, "time": now_ist()
                })
                st.success("Paper order recorded. No real broker order was sent.")

with right:
    st.markdown("### Risk")
    risk_score = st.session_state.decision["riskScore"] if st.session_state.decision else 0
    st.metric("Risk score", f"{risk_score}/100")
    st.metric("Max loss", f"₹{st.session_state.decision['maxLoss']:,.0f}" if st.session_state.decision else "—")
    st.metric("R:R", st.session_state.decision["rrRatio"] if st.session_state.decision else "—")

    st.markdown("### Paper Orders")
    if not st.session_state.paper_orders:
        st.caption("No paper orders yet.")
    for o in st.session_state.paper_orders[:5]:
        st.markdown(f"""
        <div class="card"><b>{o['side']} {o['symbol']}</b><br>
        {o['quantity']} × ₹{o['price']:,.2f}<br>
        <span class="small">{o['exchange']} · {o['time']} · PAPER ONLY</span></div>
        """, unsafe_allow_html=True)

st.divider()
st.warning("Educational/demo system. The supplied project uses simulated/static market data. This build deliberately does NOT connect to a broker or place real trades.")
