# DALAL — AI Multi-Agent Indian Market Research Agent

This is a rebuilt, runnable version of the supplied Streamlit DALAL project.

## What is included

- Streamlit dashboard
- Orchestrator agent
- Claude-powered Analyst agent
- Deterministic Risk Manager
- Paper-only Executor
- Session logs
- Paper order history
- Optional Anthropic API integration
- No real broker execution

## Run on Windows

Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Anthropic API

You can enter the API key in the dashboard, or create a `.env`/environment variable yourself.

The app uses Claude only for the Analyst stage. If no key is supplied, it runs in transparent demo mode.

## Important

The supplied original project contains static/simulated prices and UI values. This rebuild does not pretend those are live NSE/BSE values.

The Executor is intentionally paper-only. It does not connect to Zerodha, Upstox, Angel One, Fyers, or another broker and cannot place real orders.

For production use, add authenticated market-data feeds, persistent storage, proper backtesting, audit logging, broker APIs, compliance controls, and extensive testing before considering any live execution.
