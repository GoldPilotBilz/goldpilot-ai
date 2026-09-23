import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title='GoldPilot AI v1', page_icon='🥇', layout='wide')
st.title('🥇 GoldPilot AI — v1')
st.warning('ANALYSIS ONLY • No live MT5 connection • No automatic orders. Uploaded data may be delayed.')

with st.sidebar:
    st.header('Risk settings')
    reference = st.number_input('Reference balance (£)', min_value=1.0, value=10000.0, step=100.0)
    actual = st.number_input('Actual demo balance (£)', min_value=0.0, value=3737.07, step=10.0)
    use_actual = st.checkbox('Size using actual balance', value=True)
    risk_pct = st.number_input('Risk per trade (%)', min_value=0.01, max_value=5.0, value=0.5, step=0.05)
    daily_pct = st.number_input('Daily loss threshold (%)', min_value=0.1, max_value=20.0, value=3.0, step=0.5)
    min_rr = st.number_input('Minimum target R:R', min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    st.caption('Values are editable for testing; no settings are sent to MT5.')

balance = actual if use_actual else reference
risk_budget = balance * risk_pct / 100
daily_limit = balance * daily_pct / 100
c1,c2,c3 = st.columns(3)
c1.metric('Sizing balance', f'£{balance:,.2f}')
c2.metric('Planned risk / trade', f'£{risk_budget:,.2f}')
c3.metric('Daily loss threshold', f'£{daily_limit:,.2f}')

tab1,tab2,tab3 = st.tabs(['Trade planner', 'CSV analysis', 'Risk guard'])
with tab1:
    st.subheader('Manual trade planner')
    st.caption('Enter prices from your own MT5 chart. This is a calculator, not a signal.')
    direction = st.selectbox('Direction', ['BUY','SELL'])
    entry = st.number_input('Entry price (USD/oz)', min_value=0.01, value=4284.14, step=0.1, format='%.2f')
    stop = st.number_input('Stop loss (USD/oz)', min_value=0.01, value=4274.14, step=0.1, format='%.2f')
    target = st.number_input('Take profit (USD/oz)', min_value=0.01, value=4314.14, step=0.1, format='%.2f')
    valid = (stop < entry < target) if direction == 'BUY' else (target < entry < stop)
    distance = abs(entry-stop)
    rr = abs(target-entry)/distance if distance else 0
    if not valid:
        st.error('Invalid price order for this direction. BUY: SL < entry < TP. SELL: TP < entry < SL.')
    else:
        st.metric('Target risk/reward (before costs)', f'1:{rr:.2f}')
        if rr < min_rr: st.error(f'Below minimum 1:{min_rr:g}. NO TRADE under configured rule.')
        else: st.success('Price geometry meets minimum R:R. This is NOT a recommendation to enter.')
    st.divider()
    st.subheader('Broker-aware lot size — manual inputs')
    st.info('MT5 symbol contract size, minimum lot, lot step, tick value and GBP conversion must be checked before trading. This v1 calculator uses a simplified ounce-based estimate only.')
    ounces = st.number_input('Contract size (oz per 1 lot; verify in MT5)', min_value=0.001, value=100.0, step=1.0)
    gbp_per_usd = st.number_input('GBP per 1 USD (enter current conversion)', min_value=0.0001, value=0.75, step=0.001, format='%.4f')
    estimated_lots = risk_budget / (distance * ounces * gbp_per_usd) if distance else 0
    st.metric('Theoretical lot size (NOT order-ready)', f'{estimated_lots:.4f}')
    st.caption('Does not account for spread, commissions, slippage, broker lot increments, or margin. Never round up to a broker minimum lot if it exceeds risk budget.')
with tab2:
    st.subheader('Upload historical OHLC candles')
    st.caption('CSV must contain time, open, high, low, close (case-insensitive). Use closed candles only. No market data is fetched automatically.')
    upload = st.file_uploader('Choose CSV', type=['csv'])
    if upload:
        try:
            df = pd.read_csv(upload)
            df.columns = [str(c).strip().lower() for c in df.columns]
            needed = {'time','open','high','low','close'}
            if not needed.issubset(df.columns):
                st.error('Missing columns: '+', '.join(sorted(needed-set(df.columns))))
            else:
                df['time'] = pd.to_datetime(df['time'], errors='coerce', utc=True)
                for c in ['open','high','low','close']: df[c] = pd.to_numeric(df[c], errors='coerce')
                df = df.dropna(subset=['time','open','high','low','close']).sort_values('time').drop_duplicates('time')
                df = df[(df['high'] >= df[['open','close','low']].max(axis=1)) & (df['low'] <= df[['open','close','high']].min(axis=1))]
                if len(df) < 205:
                    st.warning(f'{len(df)} valid candles; at least 205 needed for EMA200 and comparison.')
                else:
                    df['ema20'] = df.close.ewm(span=20, adjust=False).mean()
                    df['ema50'] = df.close.ewm(span=50, adjust=False).mean()
                    df['ema200'] = df.close.ewm(span=200, adjust=False).mean()
                    delta = df.close.diff()
                    gains = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
                    losses = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
                    rs = gains/losses.replace(0,float('nan'))
                    df['rsi14'] = 100-100/(1+rs)
                    last = df.iloc[-1]
                    bias = 'Bullish' if last.close > last.ema20 > last.ema50 > last.ema200 else 'Bearish' if last.close < last.ema20 < last.ema50 < last.ema200 else 'Mixed / WAIT'
                    st.line_chart(df.set_index('time')[['close','ema20','ema50','ema200']].tail(200))
                    st.metric('Last uploaded close', f'${last.close:,.2f}')
                    st.metric('EMA alignment', bias)
                    st.metric('RSI(14)', 'N/A' if pd.isna(last.rsi14) else f'{last.rsi14:.1f}')
                    st.info('This is descriptive trend analysis, NOT a BUY/SELL recommendation. No backtest or predictive accuracy is claimed.')
                    st.caption('Last uploaded candle: '+str(last.time))
        except Exception as exc:
            st.error('Could not read CSV. Check its formatting. '+str(exc))
    else:
        st.info('Upload a CSV to activate the chart and indicators. No fabricated live prices are shown.')
with tab3:
    st.subheader('Daily risk guard (manual tracking)')
    realized = st.number_input('Realized losses today (£; positive number)', min_value=0.0, value=0.0, step=5.0)
    floating = st.number_input('Open-position potential loss to stop (£)', min_value=0.0, value=0.0, step=5.0)
    remaining = daily_limit-realized-floating
    st.metric('Remaining planned loss allowance', f'£{max(0,remaining):,.2f}')
    if remaining < risk_budget: st.error('NO NEW TRADE: insufficient daily loss allowance for another full-risk trade.')
    else: st.success('Allowance remains, subject to all other checks.')
    st.caption('Manual values reset when the session resets. This is not an enforced broker-side kill switch.')

st.divider()
st.caption('GoldPilot AI v1 • Educational demo dashboard • No order execution, continuous monitoring, news feed or trained prediction model.')
