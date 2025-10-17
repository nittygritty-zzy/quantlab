"""
Analysis CLI commands
"""

import click
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


@click.group()
def analyze():
    """Analyze tickers and portfolios"""
    pass


@analyze.command('ticker')
@click.argument('ticker')
@click.option('--no-options', is_flag=True, help='Skip options analysis')
@click.option('--no-fundamentals', is_flag=True, help='Skip fundamentals')
@click.option('--no-sentiment', is_flag=True, help='Skip sentiment analysis')
@click.option('--no-technicals', is_flag=True, help='Skip technical indicators')
@click.option('--output', type=click.Path(), help='Save analysis to JSON file')
@click.option('--chart', type=click.Path(), help='Generate technical chart and save to HTML file')
@click.option('--chart-days', type=int, default=90, help='Number of days for chart (default: 90)')
@click.pass_context
def analyze_ticker(ctx, ticker, no_options, no_fundamentals, no_sentiment, no_technicals, output, chart, chart_days):
    """
    Analyze a single ticker with multi-source data

    Examples:
        quantlab analyze ticker AAPL
        quantlab analyze ticker MSFT --no-options
        quantlab analyze ticker GOOGL --output analysis.json
        quantlab analyze ticker TSLA --no-technicals
    """
    try:
        analyzer = ctx.obj['analyzer']

        click.echo(f"\n🔍 Analyzing {ticker}...\n")

        # Perform analysis
        result = analyzer.analyze_ticker(
            ticker=ticker,
            include_options=not no_options,
            include_fundamentals=not no_fundamentals,
            include_sentiment=not no_sentiment,
            include_technicals=not no_technicals
        )

        if result["status"] != "success":
            click.echo(f"❌ Analysis failed: {result.get('error', 'Unknown error')}", err=True)
            return

        # Display results
        _display_ticker_analysis(result)

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)

            click.echo(f"\n💾 Analysis saved to: {output_path}")

        # Generate chart if requested
        if chart:
            try:
                click.echo(f"\n📊 Generating technical chart...")
                _generate_technical_chart(ctx, ticker, chart, chart_days)
                click.echo(f"📈 Chart saved to: {chart}")
                click.echo(f"   Open in browser to view interactive chart")
            except Exception as chart_error:
                click.echo(f"⚠️  Chart generation failed: {chart_error}", err=True)
                click.echo(f"   Analysis completed successfully, but chart could not be generated")

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)


@analyze.command('portfolio')
@click.argument('portfolio_id')
@click.option('--with-options', is_flag=True, help='Include options analysis (slow)')
@click.option('--output', type=click.Path(), help='Save analysis to JSON file')
@click.pass_context
def analyze_portfolio(ctx, portfolio_id, with_options, output):
    """
    Analyze all tickers in a portfolio

    Examples:
        quantlab analyze portfolio tech
        quantlab analyze portfolio growth --with-options
        quantlab analyze portfolio value --output portfolio_analysis.json
    """
    try:
        analyzer = ctx.obj['analyzer']

        click.echo(f"\n📊 Analyzing portfolio: {portfolio_id}...\n")

        # Perform analysis
        result = analyzer.analyze_portfolio(
            portfolio_id=portfolio_id,
            include_options=with_options
        )

        if result["status"] != "success":
            click.echo(f"❌ Analysis failed: {result.get('error', 'Unknown error')}", err=True)
            return

        # Display results
        _display_portfolio_analysis(result)

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)

            click.echo(f"\n💾 Analysis saved to: {output_path}")

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)


def _display_ticker_analysis(result):
    """Display ticker analysis results"""
    ticker = result["ticker"]

    # Price
    if result.get("price") and result["price"]:
        price = result["price"]
        click.echo(f"💰 Price: ${price['current']:.2f}")
        if price.get('change_percent'):
            sign = "+" if price['change_percent'] > 0 else ""
            click.echo(f"   Change: {sign}{price['change_percent']:.2f}%")
        click.echo(f"   Volume: {price['volume']:,}")
        click.echo()

    # Market Context
    if result.get("market_context"):
        ctx = result["market_context"]
        click.echo(f"📈 Market Context:")
        click.echo(f"   VIX: {ctx['vix']:.2f} (5d avg: {ctx['vix_5d_avg']:.2f})")
        click.echo()

    # Fundamentals
    if result.get("fundamentals"):
        fund = result["fundamentals"]
        click.echo(f"📊 Fundamentals:")
        if fund.get('pe_ratio'):
            click.echo(f"   P/E Ratio: {fund['pe_ratio']:.2f}")
        if fund.get('forward_pe'):
            click.echo(f"   Forward P/E: {fund['forward_pe']:.2f}")
        if fund.get('recommendation'):
            click.echo(f"   Recommendation: {fund['recommendation'].upper()}")
        if fund.get('target_price') and result.get('price') and result['price']:
            upside = ((float(fund['target_price']) / float(result['price']['current'])) - 1) * 100
            click.echo(f"   Target Price: ${float(fund['target_price']):.2f} ({upside:+.1f}% upside)")
        elif fund.get('target_price'):
            click.echo(f"   Target Price: ${fund['target_price']:.2f}")
        click.echo()

    # Sentiment
    if result.get("sentiment"):
        sent = result["sentiment"]
        click.echo(f"📰 News Sentiment:")
        click.echo(f"   Label: {sent['label'].upper()}")
        click.echo(f"   Score: {sent['score']:.3f}")
        click.echo(f"   Articles: {sent['articles_analyzed']} ({sent['positive_articles']} positive, {sent['negative_articles']} negative)")
        click.echo()

    # Technical Indicators
    if result.get("technical_indicators"):
        tech = result["technical_indicators"]
        click.echo(f"📉 Technical Indicators:")

        # Current price (for reference)
        if tech.get("current_price"):
            click.echo(f"   Price: ${tech['current_price']:.2f}")

        # Trend indicators
        if tech.get("trend"):
            trend = tech["trend"]
            if trend.get("sma_20"):
                click.echo(f"   SMA(20): ${trend['sma_20']:.2f}")
            if trend.get("sma_50"):
                click.echo(f"   SMA(50): ${trend['sma_50']:.2f}")

        # Momentum indicators
        if tech.get("momentum"):
            momentum = tech["momentum"]
            if momentum.get("rsi_14") is not None:
                click.echo(f"   RSI(14): {momentum['rsi_14']:.2f}")
            if momentum.get("macd_line") is not None and momentum.get("macd_signal") is not None:
                click.echo(f"   MACD: {momentum['macd_line']:.4f} / Signal: {momentum['macd_signal']:.4f}")

        # Volatility indicators
        if tech.get("volatility"):
            vol = tech["volatility"]
            if vol.get("bb_upper") and vol.get("bb_lower"):
                click.echo(f"   Bollinger Bands: ${vol['bb_lower']:.2f} - ${vol['bb_upper']:.2f}")

        # Signals
        if tech.get("signals"):
            signals = tech["signals"]
            click.echo(f"   Signals:")
            if signals.get("rsi"):
                click.echo(f"      RSI: {signals['rsi']}")
            if signals.get("macd"):
                click.echo(f"      MACD: {signals['macd']}")
            if signals.get("trend_strength"):
                click.echo(f"      Trend: {signals['trend_strength']}")

        click.echo()

    # Options
    if result.get("options"):
        opts = result["options"]

        # ITM Calls
        if opts["top_itm_calls"]:
            click.echo(f"📞 Top ITM Call Recommendations:")
            for i, call in enumerate(opts["top_itm_calls"][:3], 1):
                click.echo(f"\n   {i}. ${call['strike']:.2f} strike, expires {call['expiration']}")
                oi = f"{call['open_interest']:,}" if call.get('open_interest') is not None else "N/A"
                click.echo(f"      ITM: {call['itm_pct']:.1f}% | OI: {oi}")
                if call.get('delta') is not None and call.get('theta') is not None:
                    click.echo(f"      Delta: {call['delta']:.3f} | Theta: {call['theta']:.3f}")
                if call.get('vanna') is not None and call.get('charm') is not None:
                    click.echo(f"      Vanna: {call['vanna']:.6f} | Charm: {call['charm']:.6f}")
                click.echo(f"      Liquidity: {call['analysis']['liquidity']}")
                click.echo(f"      Score: {call['score']:.1f}/100")
            click.echo()


def _display_portfolio_analysis(result):
    """Display portfolio analysis results"""
    click.echo(f"📊 Portfolio: {result['portfolio_name']}")
    click.echo(f"   Positions: {result['num_positions']}")
    click.echo(f"   Tickers: {', '.join(result['tickers'])}")
    click.echo()

    # Aggregate metrics
    if result.get("aggregate_metrics"):
        metrics = result["aggregate_metrics"]

        if metrics.get("average_pe"):
            click.echo(f"📈 Portfolio Metrics:")
            click.echo(f"   Average P/E: {metrics['average_pe']:.2f}")
            click.echo(f"   Tickers with P/E: {metrics['tickers_with_pe']}/{result['num_positions']}")
            click.echo()

        if metrics.get("analyst_recommendations"):
            recs = metrics["analyst_recommendations"]
            total_recs = recs["buy"] + recs["hold"] + recs["sell"]
            if total_recs > 0:
                click.echo(f"💡 Analyst Recommendations:")
                click.echo(f"   Buy: {recs['buy']}")
                click.echo(f"   Hold: {recs['hold']}")
                click.echo(f"   Sell: {recs['sell']}")
                click.echo()

    # Individual ticker summaries
    click.echo(f"🔍 Ticker Summaries:")
    for ticker, analysis in result["ticker_analyses"].items():
        if analysis["status"] == "success":
            price = analysis.get("price", {}).get("current", "N/A")
            if price != "N/A":
                price_str = f"${price:.2f}"
            else:
                price_str = "N/A"

            rec = "N/A"
            if analysis.get("fundamentals"):
                rec = analysis["fundamentals"].get("recommendation", "N/A").upper()

            click.echo(f"   {ticker}: {price_str} | Recommendation: {rec}")
        else:
            click.echo(f"   {ticker}: Error - {analysis.get('error', 'Unknown')}")


def _generate_technical_chart(ctx, ticker, chart_path, days=90):
    """Generate technical analysis chart for a ticker"""
    from ..visualization import create_technical_dashboard, save_figure

    # Get data manager from analyzer
    analyzer = ctx.obj['analyzer']
    data_manager = analyzer.data

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Fetch historical data using parquet reader
    df = data_manager.parquet.get_stock_daily(
        tickers=[ticker],
        start_date=start_date,
        end_date=end_date
    )

    if df is None or df.empty:
        raise ValueError(f"No historical data available for {ticker}")

    # Filter to single ticker if multiple returned
    if 'ticker' in df.columns:
        df = df[df['ticker'] == ticker].copy()

    # Ensure date column is present
    if 'date' not in df.columns and df.index.name == 'date':
        df = df.reset_index()

    # Ensure we have the required columns
    required_cols = ['date', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Calculate technical indicators using pandas
    # RSI (simple implementation)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (2 * std)
    df['bb_lower'] = df['bb_middle'] - (2 * std)

    # Drop NaN values (from indicator calculations)
    df = df.dropna()

    if df.empty:
        raise ValueError(f"Not enough data to calculate technical indicators for {ticker}")

    # Generate chart
    fig = create_technical_dashboard(df, ticker=ticker)

    # Save chart
    chart_path = Path(chart_path)
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    save_figure(fig, str(chart_path))
