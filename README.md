# GoldPilot AI v1

Mobile-friendly Streamlit prototype. **No MT5 connection or order execution.**

## Deploy
1. Create a private GitHub repository named `goldpilot-ai`.
2. Upload `streamlit_app.py` and `requirements.txt` to the repository root.
3. Sign into https://share.streamlit.io with GitHub, select the repo and main branch, and set entrypoint `streamlit_app.py`.
4. Deploy and keep app access private. Never commit broker passwords or API keys.

## CSV
Upload CSV with headers `time,open,high,low,close`, at least 205 valid closed candles. Time is interpreted as UTC if no timezone is supplied.

## Limitations
Risk calculation is illustrative and requires broker contract specifications and current currency conversion before trading. Cloud app does not run continuously or connect to iPhone MT5. No trade execution, live news, signals, or validated predictions.
