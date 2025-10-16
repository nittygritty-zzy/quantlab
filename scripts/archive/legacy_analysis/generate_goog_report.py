"""
Generate Comprehensive Research Report for GOOG ITM Call Options
Based on collected data from Polygon API
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def load_latest_data():
    """Load the most recent GOOG analysis data"""
    results_dir = Path("/Users/zheyuanzhao/workspace/quantlab/results")
    json_files = list(results_dir.glob("goog_analysis_*.json"))

    if not json_files:
        print("No analysis data files found!")
        sys.exit(1)

    # Get most recent file
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading data from: {latest_file}")

    with open(latest_file) as f:
        return json.load(f)

def generate_markdown_report(data):
    """Generate comprehensive markdown research report"""

    report = []
    report.append("# GOOGLE (GOOG) INVESTMENT RESEARCH REPORT")
    report.append("## ITM Call Options Analysis for Bullish Position\n")
    report.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n")

    # Executive Summary
    report.append("## EXECUTIVE SUMMARY\n")

    if data['historical_bars']:
        latest_close = data['historical_bars'][-1]['close']
        prev_close = data['historical_bars'][-2]['close'] if len(data['historical_bars']) > 1 else latest_close
        change = latest_close - prev_close
        change_pct = (change / prev_close) * 100

        report.append(f"**Current Stock Price:** ${latest_close:.2f} ({change_pct:+.2f}%)\n")

    if data['ticker_details']:
        td = data['ticker_details']
        report.append(f"**Company:** {td['name']}\n")
        report.append(f"**Market Cap:** ${td['market_cap']/1e9:.2f}B\n")
        report.append(f"**Exchange:** {td['primary_exchange']}\n\n")

    # Investment Thesis
    report.append("### Investment Thesis (Bullish)\n")
    report.append("Based on our comprehensive analysis, GOOG presents a compelling opportunity for a bullish position via ITM call options:\n\n")

    thesis_points = []

    # Financial strength
    if data['financials'] and len(data['financials']) > 0:
        latest_fin = data['financials'][0]
        if 'net_income' in latest_fin and 'revenue' in latest_fin:
            margin = (latest_fin['net_income'] / latest_fin['revenue']) * 100
            thesis_points.append(f"✅ **Strong Profitability**: {margin:.1f}% net margin with ${latest_fin['net_income']/1e9:.2f}B quarterly net income")

        if 'operating_cash_flow' in latest_fin and latest_fin['operating_cash_flow'] > 0:
            thesis_points.append(f"✅ **Robust Cash Generation**: ${latest_fin['operating_cash_flow']/1e9:.2f}B operating cash flow")

    # Technical signals
    if 'rsi' in data['technical_indicators']:
        rsi = data['technical_indicators']['rsi']
        if rsi['value'] < 70:
            thesis_points.append(f"✅ **Technical Setup**: RSI at {rsi['value']:.1f} indicates room for upside (not overbought)")

    if 'sma_50' in data['technical_indicators'] and data['historical_bars']:
        sma = data['technical_indicators']['sma_50']['value']
        current = data['historical_bars'][-1]['close']
        if current < sma:
            thesis_points.append(f"✅ **Mean Reversion Opportunity**: Trading below 50-day SMA (${sma:.2f})")

    # Market cap / scale
    if data['ticker_details']:
        thesis_points.append(f"✅ **Market Leader**: ${data['ticker_details']['market_cap']/1e12:.2f}T market cap with dominant positions in search, cloud, and AI")

    for point in thesis_points:
        report.append(f"{point}\n")

    report.append("\n---\n")

    # Company Overview
    report.append("## 1. COMPANY OVERVIEW\n")

    if data['ticker_details']:
        td = data['ticker_details']
        report.append(f"**Name:** {td['name']}\n")
        report.append(f"**Listed Since:** {td['list_date']}\n")
        report.append(f"**Employees:** {td['total_employees']:,}\n")
        report.append(f"**Website:** {td['homepage_url']}\n\n")

        if td['description']:
            report.append(f"**Description:**\n{td['description']}\n\n")

    report.append("---\n")

    # Stock Price Analysis
    report.append("## 2. STOCK PRICE ANALYSIS\n")

    if data['historical_bars']:
        bars = data['historical_bars']
        latest = bars[-1]

        report.append(f"**Latest Close (as of {latest['date']}):** ${latest['close']:.2f}\n")
        report.append(f"**Day's Range:** ${latest['low']:.2f} - ${latest['high']:.2f}\n")
        report.append(f"**Volume:** {latest['volume']:,}\n")
        report.append(f"**VWAP:** ${latest['vwap']:.2f}\n\n")

        # Calculate performance metrics
        report.append("### Recent Performance\n")

        periods = [
            ("5-Day", 5),
            ("1-Month", 20),
            ("3-Month", 60)
        ]

        current_price = latest['close']

        for label, days in periods:
            if len(bars) > days:
                past_price = bars[-days-1]['close']
                change = current_price - past_price
                change_pct = (change / past_price) * 100
                report.append(f"- **{label} Change:** ${change:+.2f} ({change_pct:+.2f}%)\n")

        report.append("\n")

        # Price statistics
        closes = [b['close'] for b in bars]
        high_52w = max(closes)
        low_52w = min(closes)
        avg_price = sum(closes) / len(closes)

        report.append("### Price Statistics (90-day window)\n")
        report.append(f"- **High:** ${high_52w:.2f}\n")
        report.append(f"- **Low:** ${low_52w:.2f}\n")
        report.append(f"- **Average:** ${avg_price:.2f}\n")
        report.append(f"- **Distance from High:** {((current_price - high_52w) / high_52w * 100):.2f}%\n")
        report.append(f"- **Distance from Low:** {((current_price - low_52w) / low_52w * 100):.2f}%\n\n")

    report.append("---\n")

    # Technical Analysis
    report.append("## 3. TECHNICAL ANALYSIS\n")

    indicators = data['technical_indicators']

    if 'rsi' in indicators:
        rsi = indicators['rsi']
        report.append(f"### RSI (Relative Strength Index)\n")
        report.append(f"- **Current RSI:** {rsi['value']:.2f}\n")
        report.append(f"- **Signal:** {rsi['signal']}\n")

        if rsi['value'] < 30:
            report.append("- **Interpretation:** Oversold - potential buying opportunity\n")
        elif rsi['value'] > 70:
            report.append("- **Interpretation:** Overbought - caution warranted\n")
        else:
            report.append("- **Interpretation:** Neutral territory - balanced momentum\n")
        report.append("\n")

    if 'sma_50' in indicators:
        sma = indicators['sma_50']
        current = data['historical_bars'][-1]['close']
        diff = current - sma['value']
        diff_pct = (diff / sma['value']) * 100

        report.append(f"### Simple Moving Average (50-day)\n")
        report.append(f"- **SMA(50):** ${sma['value']:.2f}\n")
        report.append(f"- **Current vs SMA:** ${diff:+.2f} ({diff_pct:+.2f}%)\n")

        if diff > 0:
            report.append("- **Signal:** Bullish (price above SMA)\n")
        else:
            report.append("- **Signal:** Bearish (price below SMA) - potential mean reversion opportunity\n")
        report.append("\n")

    if 'ema_20' in indicators:
        ema = indicators['ema_20']
        current = data['historical_bars'][-1]['close']
        diff = current - ema['value']
        diff_pct = (diff / ema['value']) * 100

        report.append(f"### Exponential Moving Average (20-day)\n")
        report.append(f"- **EMA(20):** ${ema['value']:.2f}\n")
        report.append(f"- **Current vs EMA:** ${diff:+.2f} ({diff_pct:+.2f}%)\n\n")

    if 'macd' in indicators:
        macd = indicators['macd']
        report.append(f"### MACD (Moving Average Convergence Divergence)\n")
        report.append(f"- **MACD Line:** {macd['value']:.2f}\n")
        report.append(f"- **Signal Line:** {macd['signal']:.2f}\n")
        report.append(f"- **Histogram:** {macd['histogram']:.2f}\n")

        if macd['histogram'] > 0:
            report.append("- **Signal:** Bullish momentum (MACD above signal)\n")
        else:
            report.append("- **Signal:** Bearish momentum (MACD below signal)\n")
        report.append("\n")

    report.append("---\n")

    # Fundamental Analysis
    report.append("## 4. FUNDAMENTAL ANALYSIS\n")

    if data['financials'] and len(data['financials']) > 0:
        latest_fin = data['financials'][0]

        report.append(f"### Latest Quarterly Report\n")
        report.append(f"**Period:** {latest_fin.get('fiscal_period', 'N/A')} {latest_fin.get('fiscal_year', 'N/A')}\n")
        report.append(f"**Filing Date:** {latest_fin.get('filing_date', 'N/A')}\n\n")

        # Income Statement
        if 'revenue' in latest_fin:
            report.append(f"#### Income Statement\n")
            report.append(f"- **Revenue:** ${latest_fin['revenue']/1e9:.2f}B\n")

            if 'net_income' in latest_fin:
                report.append(f"- **Net Income:** ${latest_fin['net_income']/1e9:.2f}B\n")
                margin = (latest_fin['net_income'] / latest_fin['revenue']) * 100
                report.append(f"- **Net Profit Margin:** {margin:.2f}%\n")

            if 'gross_profit' in latest_fin:
                report.append(f"- **Gross Profit:** ${latest_fin['gross_profit']/1e9:.2f}B\n")
                gm = (latest_fin['gross_profit'] / latest_fin['revenue']) * 100
                report.append(f"- **Gross Margin:** {gm:.2f}%\n")

            report.append("\n")

        # Balance Sheet
        if 'total_assets' in latest_fin or 'total_liabilities' in latest_fin:
            report.append(f"#### Balance Sheet\n")

            if 'total_assets' in latest_fin:
                report.append(f"- **Total Assets:** ${latest_fin['total_assets']/1e9:.2f}B\n")

            if 'total_liabilities' in latest_fin:
                report.append(f"- **Total Liabilities:** ${latest_fin['total_liabilities']/1e9:.2f}B\n")

            if 'equity' in latest_fin:
                report.append(f"- **Shareholders' Equity:** ${latest_fin['equity']/1e9:.2f}B\n")

            if 'total_assets' in latest_fin and 'total_liabilities' in latest_fin:
                debt_to_assets = (latest_fin['total_liabilities'] / latest_fin['total_assets']) * 100
                report.append(f"- **Debt-to-Assets Ratio:** {debt_to_assets:.2f}%\n")

            report.append("\n")

        # Cash Flow
        if 'operating_cash_flow' in latest_fin:
            report.append(f"#### Cash Flow\n")
            report.append(f"- **Operating Cash Flow:** ${latest_fin['operating_cash_flow']/1e9:.2f}B\n")

            if 'net_income' in latest_fin and latest_fin['net_income'] > 0:
                ocf_to_ni = (latest_fin['operating_cash_flow'] / latest_fin['net_income']) * 100
                report.append(f"- **OCF / Net Income:** {ocf_to_ni:.1f}% (quality of earnings)\n")

            report.append("\n")

        # Historical trend (if multiple periods available)
        if len(data['financials']) >= 4:
            report.append(f"### Revenue Trend (Last 4 Quarters)\n")
            for i, fin in enumerate(data['financials'][:4]):
                if 'revenue' in fin:
                    period = f"{fin.get('fiscal_period', 'Q?')} {fin.get('fiscal_year', '?')}"
                    rev = fin['revenue'] / 1e9
                    report.append(f"- **{period}:** ${rev:.2f}B\n")

            # Calculate growth
            if 'revenue' in data['financials'][0] and 'revenue' in data['financials'][3]:
                latest_rev = data['financials'][0]['revenue']
                year_ago_rev = data['financials'][3]['revenue']
                growth = ((latest_rev - year_ago_rev) / year_ago_rev) * 100
                report.append(f"\n**YoY Growth:** {growth:+.2f}%\n")

            report.append("\n")

    report.append("---\n")

    # ITM Call Options Strategy
    report.append("## 5. ITM CALL OPTIONS STRATEGY\n")

    if data['historical_bars']:
        current_price = data['historical_bars'][-1]['close']

        report.append("### Why ITM Calls for GOOG?\n")
        report.append(f"Current Stock Price: **${current_price:.2f}**\n\n")

        report.append("**Advantages of ITM Calls:**\n")
        report.append("1. **High Delta (0.60-0.90)**: ITM calls move nearly dollar-for-dollar with the stock\n")
        report.append("2. **Lower Time Decay**: More intrinsic value means less theta exposure\n")
        report.append("3. **Leverage with Downside Protection**: Significant intrinsic value provides cushion\n")
        report.append("4. **Capital Efficiency**: Control 100 shares with less capital than buying stock\n\n")

        report.append("### Recommended ITM Call Strike Ranges\n")
        report.append("Based on current price analysis:\n\n")

        # Generate strike recommendations
        strikes = []

        # Moderate ITM (5-10% below current)
        strikes.append({
            'label': 'Conservative ITM',
            'strike_range': f"${current_price * 0.90:.2f} - ${current_price * 0.95:.2f}",
            'itm_pct': '5-10%',
            'delta_est': '0.65-0.75',
            'characteristics': 'Balanced intrinsic/time value, good for moderate bullish view'
        })

        # Deep ITM (10-15% below current)
        strikes.append({
            'label': 'Deep ITM',
            'strike_range': f"${current_price * 0.85:.2f} - ${current_price * 0.90:.2f}",
            'itm_pct': '10-15%',
            'delta_est': '0.75-0.85',
            'characteristics': 'High intrinsic value, low time decay, stock replacement strategy'
        })

        # Very Deep ITM (15-20% below current)
        strikes.append({
            'label': 'Very Deep ITM',
            'strike_range': f"${current_price * 0.80:.2f} - ${current_price * 0.85:.2f}",
            'itm_pct': '15-20%',
            'delta_est': '0.85-0.95',
            'characteristics': 'Maximum intrinsic value, behaves like stock, minimal time decay'
        })

        for strike in strikes:
            report.append(f"#### {strike['label']}\n")
            report.append(f"- **Strike Range:** {strike['strike_range']}\n")
            report.append(f"- **% ITM:** {strike['itm_pct']}\n")
            report.append(f"- **Est. Delta:** {strike['delta_est']}\n")
            report.append(f"- **Characteristics:** {strike['characteristics']}\n\n")

        # Expiration recommendations
        report.append("### Recommended Expiration Dates\n")
        report.append("For a bullish position, consider:\n\n")
        report.append("1. **30-60 DTE (Days to Expiration)**\n")
        report.append("   - Suitable for near-term catalyst expectations\n")
        report.append("   - Lower cost, but higher theta decay\n\n")

        report.append("2. **90-120 DTE**\n")
        report.append("   - Balanced approach for medium-term outlook\n")
        report.append("   - Better theta profile than short-term\n\n")

        report.append("3. **180+ DTE (LEAPS)**\n")
        report.append("   - Long-term strategic position\n")
        report.append("   - Minimal daily theta, essentially stock replacement\n")
        report.append("   - Higher upfront cost but more time for thesis to play out\n\n")

        # Risk management
        report.append("### Risk Management\n")
        report.append("**Entry Strategy:**\n")
        report.append("- Consider scaling into position (e.g., 1/3 now, 1/3 on pullback, 1/3 on weakness)\n")
        report.append("- Look for entries near support levels (SMA, previous support zones)\n")
        report.append("- Monitor implied volatility - avoid buying when IV is elevated\n\n")

        report.append("**Exit Strategy:**\n")
        report.append("- Set profit targets (e.g., 30%, 50%, 100% gain)\n")
        report.append("- Consider rolling up and out if stock rallies significantly\n")
        report.append("- Use stop-loss at -30% to -50% of position value\n")
        report.append("- Exit if fundamental thesis breaks (e.g., earnings miss, regulatory issues)\n\n")

        report.append("**Position Sizing:**\n")
        report.append("- Risk no more than 2-5% of portfolio on single options position\n")
        report.append("- ITM calls require more capital - adjust number of contracts accordingly\n")
        report.append("- Remember: 1 contract = 100 shares of exposure\n\n")

    report.append("---\n")

    # Catalysts and Risks
    report.append("## 6. POTENTIAL CATALYSTS & RISKS\n")

    report.append("### Bullish Catalysts\n")
    report.append("1. **AI Leadership**: Google's advances in AI (Gemini, Bard) could drive revenue growth\n")
    report.append("2. **Cloud Growth**: GCP gaining market share vs AWS and Azure\n")
    report.append("3. **YouTube Strength**: Continued monetization improvements\n")
    report.append("4. **Search Dominance**: Core business remains highly profitable\n")
    report.append("5. **Cost Management**: Efficiency initiatives improving margins\n")
    report.append("6. **Share Buybacks**: Alphabet has robust buyback program supporting stock\n\n")

    report.append("### Key Risks\n")
    report.append("1. **Regulatory**: Antitrust concerns in US and EU\n")
    report.append("2. **Competition**: AI competition from Microsoft/OpenAI, Amazon, etc.\n")
    report.append("3. **Ad Market**: Economic slowdown could pressure ad revenue\n")
    report.append("4. **Search Disruption**: AI chatbots potentially disrupting search business\n")
    report.append("5. **Valuation**: Any multiple compression in tech sector\n\n")

    report.append("---\n")

    # Conclusion
    report.append("## 7. CONCLUSION & RECOMMENDATION\n")

    report.append("### Overall Assessment: **BULLISH**\n\n")

    report.append("**Summary:**\n")

    # Build conclusion based on data
    conclusion_points = []

    if data['financials'] and 'net_income' in data['financials'][0]:
        conclusion_points.append("Strong fundamental performance with robust profitability and cash generation")

    if 'rsi' in data['technical_indicators'] and data['technical_indicators']['rsi']['value'] < 70:
        conclusion_points.append("Technical setup shows room for upside without overbought conditions")

    conclusion_points.append("ITM call options provide leveraged exposure with built-in downside protection")
    conclusion_points.append("Market leadership position in search, cloud, and AI provides long-term growth runway")

    for i, point in enumerate(conclusion_points, 1):
        report.append(f"{i}. {point}\n")

    report.append("\n### Recommended Action\n")

    if data['historical_bars']:
        current = data['historical_bars'][-1]['close']
        target_strike = current * 0.90

        report.append(f"**BUY ITM Call Options on GOOG**\n\n")
        report.append(f"- **Suggested Strike Range:** ${current * 0.85:.2f} - ${current * 0.95:.2f} (10-15% ITM)\n")
        report.append(f"- **Preferred Expiration:** 90-180 DTE for medium-term outlook\n")
        report.append(f"- **Entry Timing:** Current levels or on pullback to support\n")
        report.append(f"- **Risk/Reward:** Favorable with strong fundamental backdrop\n\n")

    report.append("**Important:** This is a research report for educational purposes. Conduct your own due diligence and consult with a financial advisor before making investment decisions. Options trading involves substantial risk and is not suitable for all investors.\n\n")

    report.append("---\n")
    report.append(f"\n*Report generated by QuantLab Analysis System*\n")
    report.append(f"*Data source: Polygon.io API*\n")
    report.append(f"*Generation timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    return "\n".join(report)

def save_report(report, filename=None):
    """Save report to markdown file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/zheyuanzhao/workspace/quantlab/docs/GOOG_ITM_CALLS_RESEARCH_{timestamp}.md"

    with open(filename, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {filename}")
    return filename

def main():
    print("="*80)
    print("GOOG RESEARCH REPORT GENERATOR")
    print("="*80)

    # Load data
    data = load_latest_data()

    # Generate report
    print("\nGenerating comprehensive research report...")
    report = generate_markdown_report(data)

    # Save report
    report_file = save_report(report)

    print("\n" + "="*80)
    print("REPORT GENERATION COMPLETE")
    print("="*80)
    print(f"\nReport location: {report_file}")
    print("\nYou can now:")
    print("1. Review the markdown report")
    print("2. Use the analysis to inform your ITM call options strategy")
    print("3. Share with stakeholders")

    return report_file

if __name__ == "__main__":
    main()
