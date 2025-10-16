"""
GOOG LEAP Call Analysis
Analyzes long-term call options (>1 year) for GOOG
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, date
from quantlab.utils.config import load_config
from quantlab.data.database import DatabaseManager
from quantlab.data.parquet_reader import ParquetReader
from quantlab.data.data_manager import DataManager

# Initialize
config = load_config()
db = DatabaseManager(config.database_path)
parquet = ParquetReader(config.parquet_root)
data_mgr = DataManager(config, db, parquet)

print("\n" + "="*70)
print("GOOG LEAP CALL ANALYSIS")
print("="*70 + "\n")

# Get current price
ticker = "GOOG"
price_data = data_mgr.get_stock_price(ticker)
current_price = float(price_data.close) if price_data else None

if not current_price:
    print("❌ Could not get current price")
    sys.exit(1)

print(f"📊 Current Stock Price: ${current_price:.2f}\n")

# Analyze January 2027 LEAPs (classic LEAP expiration)
leap_date = date(2027, 1, 15)
print(f"🎯 Analyzing LEAP Calls expiring {leap_date}...")
print(f"   Days to expiration: {(leap_date - date.today()).days} days\n")

# Get LEAP call options (ATM to 10% OTM for LEAPs)
leap_calls = data_mgr.get_options_chain(
    ticker=ticker,
    expiration_date=leap_date,
    option_type="call",
    min_itm_pct=-10.0,  # Up to 10% OTM
    max_itm_pct=10.0,   # Up to 10% ITM
    use_cache=False
)

print(f"✓ Found {len(leap_calls)} LEAP call contracts in ATM range (-10% to +10%)\n")

if not leap_calls:
    print("❌ No LEAP calls found in target range")
    sys.exit(1)

# Sort by score (from options analyzer)
leap_calls_sorted = sorted(leap_calls, key=lambda x: (
    x.open_interest if x.open_interest else 0,  # Prefer liquidity
    abs(x.delta - 0.7) if x.delta else 1.0       # Prefer delta ~0.7
), reverse=True)

print("📞 TOP 5 LEAP CALL RECOMMENDATIONS:\n")
print(f"{'#':<3} {'Strike':<10} {'ITM%':<8} {'Price':<10} {'OI':<10} {'Delta':<8} {'Theta':<10} {'Vanna':<12}")
print("-" * 90)

for i, call in enumerate(leap_calls_sorted[:5], 1):
    strike = call.strike_price
    itm_pct = call.itm_percentage
    price = f"${call.last_price:.2f}" if call.last_price else "N/A"
    oi = f"{call.open_interest:,}" if call.open_interest else "N/A"
    delta = f"{call.delta:.3f}" if call.delta else "N/A"
    theta = f"{call.theta:.3f}" if call.theta else "N/A"
    vanna = f"{call.vanna:.6f}" if call.vanna else "N/A"

    print(f"{i:<3} ${strike:<9.2f} {itm_pct:>6.1f}% {price:<10} {oi:<10} {delta:<8} {theta:<10} {vanna:<12}")

print("\n" + "="*70)
print("DETAILED ANALYSIS OF TOP 3 LEAP CALLS:")
print("="*70 + "\n")

for i, call in enumerate(leap_calls_sorted[:3], 1):
    print(f"#{i}: ${call.strike_price:.2f} Strike (Expires {call.expiration_date})")
    print(f"   Contract: {call.contract_ticker}")
    print(f"   ITM Percentage: {call.itm_percentage:.2f}%")
    print(f"   ")
    print(f"   Pricing:")
    print(f"      Bid: ${call.bid:.2f}" if call.bid else "      Bid: N/A")
    print(f"      Ask: ${call.ask:.2f}" if call.ask else "      Ask: N/A")
    print(f"      Last: ${call.last_price:.2f}" if call.last_price else "      Last: N/A")
    print(f"   ")
    print(f"   Liquidity:")
    print(f"      Open Interest: {call.open_interest:,}" if call.open_interest else "      Open Interest: N/A")
    print(f"      Volume: {call.volume:,}" if call.volume else "      Volume: N/A")
    print(f"   ")
    if call.delta:
        print(f"   Greeks:")
        print(f"      Delta (Δ): {call.delta:.4f}  - {call.delta * 100:.1f}% of stock movement")
        print(f"      Gamma (Γ): {call.gamma:.4f}  - Delta change per $1 move" if call.gamma else "")
        print(f"      Theta (Θ): {call.theta:.4f}  - ${abs(call.theta):.2f} daily time decay" if call.theta else "")
        print(f"      Vega (ν):  {call.vega:.4f}  - ${call.vega:.2f} per 1% IV change" if call.vega else "")
        print(f"   ")
        print(f"   Advanced Greeks:")
        print(f"      Vanna: {call.vanna:.6f}  - Delta sensitivity to IV" if call.vanna else "")
        print(f"      Charm: {call.charm:.6f}  - Delta decay over time" if call.charm else "")
        print(f"      Vomma: {call.vomma:.6f}  - Vega sensitivity to IV" if call.vomma else "")
    print(f"   ")

    # Analysis
    print(f"   📊 Analysis:")
    if call.delta and call.delta >= 0.6:
        print(f"      ✓ High delta ({call.delta:.2f}) - Strong correlation to stock price")
    elif call.delta and call.delta >= 0.4:
        print(f"      • Moderate delta ({call.delta:.2f}) - Balanced risk/reward")

    if call.theta and abs(call.theta) < 0.05:
        print(f"      ✓ Low time decay (${abs(call.theta):.3f}/day) - Good for long-term holds")

    if call.open_interest and call.open_interest > 100:
        print(f"      ✓ Good liquidity (OI: {call.open_interest:,})")
    elif call.open_interest:
        print(f"      ⚠ Low liquidity (OI: {call.open_interest:,}) - May have wide spreads")

    print()

print("="*70)
print("RECOMMENDATION SUMMARY")
print("="*70 + "\n")

if leap_calls_sorted:
    top_call = leap_calls_sorted[0]
    print(f"🎯 Best LEAP Call: ${top_call.strike_price:.2f} strike")
    print(f"   Current Stock: ${current_price:.2f}")
    print(f"   Strike Price: ${top_call.strike_price:.2f}")
    print(f"   ITM Amount: {top_call.itm_percentage:.2f}%")
    print(f"   Days to Expiry: {(leap_date - date.today()).days} days")
    print(f"   Delta: {top_call.delta:.3f}" if top_call.delta else "")
    print()

    intrinsic = max(0, current_price - top_call.strike_price)
    if top_call.last_price:
        extrinsic = top_call.last_price - intrinsic
        print(f"   Intrinsic Value: ${intrinsic:.2f}")
        print(f"   Time Value: ${extrinsic:.2f}")
        print(f"   Total Premium: ${top_call.last_price:.2f}")
        print()

        # Break-even
        breakeven = top_call.strike_price + top_call.last_price
        breakeven_pct = ((breakeven / current_price) - 1) * 100
        print(f"   Break-Even Price: ${breakeven:.2f} (+{breakeven_pct:.1f}%)")
        print(f"   Required Stock Move: ${breakeven - current_price:.2f}")
        print()

print("="*70)
print("\n✅ Analysis complete!\n")
