"""
Stock Screener CLI commands
"""

import click
import json
import pandas as pd
from pathlib import Path
from tabulate import tabulate

from ..core.screener import ScreenCriteria, StockScreener


@click.group()
def screen():
    """Stock screening commands"""
    pass


@screen.command('technical')
@click.option('--rsi-min', type=float, help='Minimum RSI value (e.g., 30 for oversold)')
@click.option('--rsi-max', type=float, help='Maximum RSI value (e.g., 70 for overbought)')
@click.option('--macd-signal', type=click.Choice(['bullish', 'bearish']), help='MACD signal filter')
@click.option('--sma-crossover', type=click.Choice(['golden', 'death']), help='SMA crossover pattern')
@click.option('--price-above-sma20', is_flag=True, help='Price above SMA20')
@click.option('--price-above-sma50', is_flag=True, help='Price above SMA50')
@click.option('--bb-position', type=click.Choice(['above_upper', 'below_lower', 'middle']),
              help='Bollinger Bands position')
@click.option('--adx-min', type=float, help='Minimum ADX (25+ indicates strong trend)')
@click.option('--volume-min', type=int, help='Minimum daily volume')
@click.option('--price-min', type=float, help='Minimum price')
@click.option('--price-max', type=float, help='Maximum price')
@click.option('--limit', default=50, help='Maximum results (default: 50)')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
@click.pass_context
def screen_technical(ctx, rsi_min, rsi_max, macd_signal, sma_crossover,
                     price_above_sma20, price_above_sma50, bb_position, adx_min,
                     volume_min, price_min, price_max, limit, output):
    """
    Screen stocks by technical indicators

    Examples:

      # Find oversold stocks (RSI < 30)
      quantlab screen technical --rsi-max 30 --volume-min 1000000

      # Find stocks with bullish MACD and strong trend
      quantlab screen technical --macd-signal bullish --adx-min 25

      # Find golden cross patterns
      quantlab screen technical --sma-crossover golden --limit 20
    """
    try:
        # Create criteria
        criteria = ScreenCriteria(
            rsi_min=rsi_min,
            rsi_max=rsi_max,
            macd_signal=macd_signal,
            sma_crossover=sma_crossover,
            price_above_sma20=price_above_sma20 if price_above_sma20 else None,
            price_above_sma50=price_above_sma50 if price_above_sma50 else None,
            bb_position=bb_position,
            adx_min=adx_min,
            volume_min=volume_min,
            price_min=price_min,
            price_max=price_max
        )

        # Run screener
        screener = _get_screener(ctx)
        click.echo("\n🔍 Screening stocks by technical criteria...\n")

        results = screener.screen(criteria, limit=limit)

        # Display results
        _display_results(results, output, "Technical Screen")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('fundamental')
@click.option('--pe-min', type=float, help='Minimum P/E ratio')
@click.option('--pe-max', type=float, help='Maximum P/E ratio (e.g., 20 for value stocks)')
@click.option('--forward-pe-max', type=float, help='Maximum forward P/E ratio')
@click.option('--peg-ratio-max', type=float, help='Maximum PEG ratio (<1 is good)')
@click.option('--revenue-growth-min', type=float, help='Minimum revenue growth % (e.g., 10)')
@click.option('--profit-margin-min', type=float, help='Minimum profit margin %')
@click.option('--roe-min', type=float, help='Minimum return on equity %')
@click.option('--debt-equity-max', type=float, help='Maximum debt/equity ratio')
@click.option('--market-cap-min', type=float, help='Minimum market cap in billions')
@click.option('--market-cap-max', type=float, help='Maximum market cap in billions')
@click.option('--min-analysts', type=int, help='Minimum analyst coverage')
@click.option('--recommendation', type=click.Choice(['buy', 'hold', 'sell']), help='Analyst recommendation')
@click.option('--limit', default=50, help='Maximum results (default: 50)')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
@click.pass_context
def screen_fundamental(ctx, pe_min, pe_max, forward_pe_max, peg_ratio_max,
                       revenue_growth_min, profit_margin_min, roe_min, debt_equity_max,
                       market_cap_min, market_cap_max, min_analysts, recommendation,
                       limit, output):
    """
    Screen stocks by fundamental data

    Examples:

      # Find value stocks (low P/E, good growth)
      quantlab screen fundamental --pe-max 20 --revenue-growth-min 10

      # Find high-quality growth stocks
      quantlab screen fundamental --revenue-growth-min 20 --profit-margin-min 15 --debt-equity-max 1.0

      # Find large-cap value stocks
      quantlab screen fundamental --pe-max 15 --market-cap-min 50 --roe-min 15
    """
    try:
        # Create criteria
        criteria = ScreenCriteria(
            pe_min=pe_min,
            pe_max=pe_max,
            forward_pe_max=forward_pe_max,
            peg_ratio_max=peg_ratio_max,
            revenue_growth_min=revenue_growth_min,
            profit_margin_min=profit_margin_min,
            roe_min=roe_min,
            debt_equity_max=debt_equity_max,
            market_cap_min=market_cap_min,
            market_cap_max=market_cap_max,
            min_analysts=min_analysts,
            recommendation=recommendation
        )

        # Run screener
        screener = _get_screener(ctx)
        click.echo("\n🔍 Screening stocks by fundamental criteria...\n")
        click.echo("⚠️  Note: This requires API calls and may take a few minutes\n")

        results = screener.screen(criteria, limit=limit)

        # Display results
        _display_results(results, output, "Fundamental Screen")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('combined')
@click.option('--rsi-max', type=float, help='Maximum RSI (oversold if < 30)')
@click.option('--macd-signal', type=click.Choice(['bullish', 'bearish']), help='MACD signal')
@click.option('--pe-max', type=float, help='Maximum P/E ratio')
@click.option('--revenue-growth-min', type=float, help='Minimum revenue growth %')
@click.option('--profit-margin-min', type=float, help='Minimum profit margin %')
@click.option('--debt-equity-max', type=float, help='Maximum debt/equity ratio')
@click.option('--sentiment-min', type=float, help='Minimum sentiment score (0-1)')
@click.option('--volume-min', type=int, help='Minimum daily volume')
@click.option('--market-cap-min', type=float, help='Minimum market cap in billions')
@click.option('--limit', default=50, help='Maximum results (default: 50)')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
@click.pass_context
def screen_combined(ctx, rsi_max, macd_signal, pe_max, revenue_growth_min,
                    profit_margin_min, debt_equity_max, sentiment_min, volume_min,
                    market_cap_min, limit, output):
    """
    Screen stocks with combined criteria (technical + fundamental + sentiment)

    Examples:

      # Find undervalued oversold stocks
      quantlab screen combined --rsi-max 35 --pe-max 20 --revenue-growth-min 10

      # Find high-quality stocks with positive momentum
      quantlab screen combined --macd-signal bullish --profit-margin-min 15 --sentiment-min 0.6

      # Find large-cap value opportunities
      quantlab screen combined --pe-max 15 --market-cap-min 50 --debt-equity-max 1.5
    """
    try:
        # Create criteria
        criteria = ScreenCriteria(
            rsi_max=rsi_max,
            macd_signal=macd_signal,
            pe_max=pe_max,
            revenue_growth_min=revenue_growth_min,
            profit_margin_min=profit_margin_min,
            debt_equity_max=debt_equity_max,
            sentiment_min=sentiment_min,
            volume_min=volume_min,
            market_cap_min=market_cap_min
        )

        # Run screener
        screener = _get_screener(ctx)
        click.echo("\n🔍 Screening stocks with combined criteria...\n")
        click.echo("⚠️  Note: This requires API calls and may take several minutes\n")

        results = screener.screen(criteria, limit=limit, include_score=True)

        # Display results
        _display_results(results, output, "Combined Screen")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('preset')
@click.argument('preset_name', type=click.Choice([
    'value-stocks', 'growth-stocks', 'oversold', 'overbought',
    'momentum', 'quality', 'dividend-yield'
]))
@click.option('--limit', default=50, help='Maximum results (default: 50)')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
@click.pass_context
def screen_preset(ctx, preset_name, limit, output):
    """
    Run preset screening strategy

    Available presets:

      value-stocks       Low P/E, good fundamentals
      growth-stocks      High revenue growth, strong margins
      oversold           RSI < 30, high volume
      overbought         RSI > 70, potential reversal
      momentum           Bullish MACD, strong trend (ADX > 25)
      quality            High profit margins, low debt, good growth
      dividend-yield     High dividend yield stocks (NOT YET IMPLEMENTED)

    Examples:

      quantlab screen preset value-stocks --limit 20
      quantlab screen preset oversold --output results/oversold.json
    """
    try:
        # Define presets
        presets = {
            'value-stocks': ScreenCriteria(
                pe_max=15,
                debt_equity_max=1.5,
                revenue_growth_min=5,
                profit_margin_min=10,
                volume_min=500000
            ),
            'growth-stocks': ScreenCriteria(
                revenue_growth_min=20,
                profit_margin_min=15,
                market_cap_min=1.0,
                volume_min=1000000
            ),
            'oversold': ScreenCriteria(
                rsi_max=30,
                volume_min=1000000,
                price_min=5.0
            ),
            'overbought': ScreenCriteria(
                rsi_min=70,
                volume_min=1000000,
                price_min=5.0
            ),
            'momentum': ScreenCriteria(
                macd_signal='bullish',
                adx_min=25,
                volume_min=1000000,
                price_above_sma50=True
            ),
            'quality': ScreenCriteria(
                profit_margin_min=20,
                debt_equity_max=1.0,
                revenue_growth_min=10,
                roe_min=15
            )
        }

        if preset_name not in presets:
            click.echo(f"❌ Unknown preset: {preset_name}")
            click.echo(f"Available presets: {', '.join(presets.keys())}")
            return

        criteria = presets[preset_name]

        # Run screener
        screener = _get_screener(ctx)
        click.echo(f"\n🔍 Running preset screen: {preset_name}\n")

        results = screener.screen(criteria, limit=limit, include_score=True)

        # Display results
        _display_results(results, output, f"Preset: {preset_name}")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('custom')
@click.option('--universe', multiple=True, help='Specific tickers to screen (can specify multiple times)')
@click.option('--universe-file', type=click.Path(exists=True), help='File with tickers (one per line)')
@click.option('--rsi-min', type=float)
@click.option('--rsi-max', type=float)
@click.option('--pe-max', type=float)
@click.option('--revenue-growth-min', type=float)
@click.option('--volume-min', type=int)
@click.option('--limit', default=100, help='Maximum results (default: 100)')
@click.option('--workers', default=4, help='Parallel workers (default: 4)')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
@click.pass_context
def screen_custom(ctx, universe, universe_file, rsi_min, rsi_max, pe_max, revenue_growth_min,
                 volume_min, limit, workers, output):
    """
    Custom screening with flexible criteria and universe selection

    Examples:

      # Screen specific tickers
      quantlab screen custom --universe AAPL --universe MSFT --universe GOOGL --rsi-max 40

      # Screen from file
      quantlab screen custom --universe-file my_watchlist.txt --pe-max 20
    """
    try:
        # Load universe
        ticker_universe = None
        if universe:
            ticker_universe = list(universe)
        elif universe_file:
            with open(universe_file, 'r') as f:
                ticker_universe = [line.strip() for line in f if line.strip()]

        # Create criteria
        criteria = ScreenCriteria(
            rsi_min=rsi_min,
            rsi_max=rsi_max,
            pe_max=pe_max,
            revenue_growth_min=revenue_growth_min,
            volume_min=volume_min
        )

        # Run screener
        screener = _get_screener(ctx)

        if ticker_universe:
            click.echo(f"\n🔍 Screening {len(ticker_universe)} specified tickers...\n")
        else:
            click.echo("\n🔍 Screening entire universe...\n")

        results = screener.screen(criteria, universe=ticker_universe, limit=limit, workers=workers)

        # Display results
        _display_results(results, output, "Custom Screen")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('score')
@click.option('--universe', multiple=True, help='Specific tickers to screen')
@click.option('--universe-file', type=click.Path(exists=True), help='File with tickers')
@click.option('--rsi-min', type=float)
@click.option('--rsi-max', type=float)
@click.option('--macd-signal', type=click.Choice(['bullish', 'bearish']))
@click.option('--pe-max', type=float)
@click.option('--revenue-growth-min', type=float)
@click.option('--profit-margin-min', type=float)
@click.option('--debt-equity-max', type=float)
@click.option('--volume-min', type=int)
@click.option('--market-cap-min', type=float)
@click.option('--weight-technical', default=0.3, help='Weight for technical score (default: 0.3)')
@click.option('--weight-fundamental', default=0.4, help='Weight for fundamental score (default: 0.4)')
@click.option('--weight-sentiment', default=0.3, help='Weight for sentiment score (default: 0.3)')
@click.option('--limit', default=50)
@click.option('--workers', default=4, help='Parallel workers')
@click.option('--output', type=click.Path())
@click.pass_context
def screen_weighted(ctx, universe, universe_file, rsi_min, rsi_max, macd_signal,
                   pe_max, revenue_growth_min, profit_margin_min, debt_equity_max,
                   volume_min, market_cap_min,
                   weight_technical, weight_fundamental, weight_sentiment,
                   limit, workers, output):
    """
    Screen with custom scoring weights

    Allows you to prioritize different factors:
    - Technical (momentum, trend)
    - Fundamental (valuation, growth, quality)
    - Sentiment (news, analyst ratings)

    Examples:

      # Prioritize fundamentals (60%)
      quantlab screen score \\
          --weight-technical 0.2 \\
          --weight-fundamental 0.6 \\
          --weight-sentiment 0.2 \\
          --pe-max 20 --revenue-growth-min 10

      # Balanced approach
      quantlab screen score \\
          --weight-technical 0.33 \\
          --weight-fundamental 0.34 \\
          --weight-sentiment 0.33
    """
    try:
        # Load universe if specified
        ticker_universe = None
        if universe:
            ticker_universe = list(universe)
        elif universe_file:
            with open(universe_file, 'r') as f:
                ticker_universe = [line.strip() for line in f if line.strip()]

        # Create criteria
        criteria = ScreenCriteria(
            rsi_min=rsi_min,
            rsi_max=rsi_max,
            macd_signal=macd_signal,
            pe_max=pe_max,
            revenue_growth_min=revenue_growth_min,
            profit_margin_min=profit_margin_min,
            debt_equity_max=debt_equity_max,
            volume_min=volume_min,
            market_cap_min=market_cap_min
        )

        # Run weighted screener
        screener = _get_screener(ctx)
        click.echo(f"\n🔍 Weighted screening (tech={weight_technical}, fund={weight_fundamental}, sent={weight_sentiment})...\n")

        results = screener.screen_with_weights(
            criteria,
            weight_technical=weight_technical,
            weight_fundamental=weight_fundamental,
            weight_sentiment=weight_sentiment,
            universe=ticker_universe,
            limit=limit,
            workers=workers
        )

        # Display results
        _display_results(results, output, "Weighted Screen")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('similar')
@click.argument('portfolio_id')
@click.option('--limit', default=20, help='Maximum results (default: 20)')
@click.option('--min-score', default=60.0, help='Minimum similarity score (default: 60)')
@click.option('--output', type=click.Path())
@click.pass_context
def screen_similar(ctx, portfolio_id, limit, min_score, output):
    """
    Find stocks similar to an existing portfolio

    Analyzes your portfolio's characteristics (P/E, growth, margins, etc.)
    and finds similar stocks you don't already own.

    Examples:

      # Find stocks similar to your tech portfolio
      quantlab screen similar tech_giants --limit 10

      # Higher similarity threshold
      quantlab screen similar value_portfolio --min-score 75 --limit 15
    """
    try:
        screener = _get_screener(ctx)
        click.echo(f"\n🔍 Finding stocks similar to portfolio: {portfolio_id}\n")

        results = screener.find_similar_to_portfolio(
            portfolio_id=portfolio_id,
            limit=limit,
            min_score=min_score
        )

        # Display results
        _display_results(results, output, f"Similar to {portfolio_id}")

    except Exception as e:
        click.echo(f"❌ Screening failed: {e}", err=True)


@screen.command('compare')
@click.argument('file1', type=click.Path(exists=True))
@click.argument('file2', type=click.Path(exists=True))
@click.option('--name1', default="Screen 1", help='Name for first screen')
@click.option('--name2', default="Screen 2", help='Name for second screen')
@click.option('--output', type=click.Path(), help='Save comparison to JSON')
@click.pass_context
def screen_compare(ctx, file1, file2, name1, name2, output):
    """
    Compare two screening results

    Shows overlap, unique stocks, and statistics.

    Examples:

      # Compare value vs growth screens
      quantlab screen compare results/value.json results/growth.json \\
          --name1 "Value Stocks" --name2 "Growth Stocks"

      # Compare oversold on different days
      quantlab screen compare results/oversold_20251015.json results/oversold_20251016.json
    """
    try:
        # Load screen results
        import json

        with open(file1, 'r') as f:
            data1 = json.load(f)
            results1 = pd.DataFrame(data1.get('results', []))

        with open(file2, 'r') as f:
            data2 = json.load(f)
            results2 = pd.DataFrame(data2.get('results', []))

        # Compare
        screener = _get_screener(ctx)
        comparison = screener.compare_screens(results1, results2, name1, name2)

        # Display results
        click.echo(f"\n📊 Screen Comparison\n")
        click.echo(f"{'='*60}\n")

        click.echo(f"{comparison['screen1']['name']}: {comparison['screen1']['count']} stocks")
        click.echo(f"{comparison['screen2']['name']}: {comparison['screen2']['count']} stocks\n")

        click.echo(f"Overlap: {comparison['overlap']['count']} stocks ({comparison['overlap']['percentage']:.1f}%)")
        if comparison['overlap']['tickers']:
            click.echo(f"  {', '.join(comparison['overlap']['tickers'][:10])}")
            if len(comparison['overlap']['tickers']) > 10:
                click.echo(f"  ... and {len(comparison['overlap']['tickers']) - 10} more\n")
        else:
            click.echo()

        click.echo(f"Only in {name1}: {comparison['only_in_screen1']['count']} stocks")
        if comparison['only_in_screen1']['tickers']:
            click.echo(f"  {', '.join(comparison['only_in_screen1']['tickers'][:10])}")
            if len(comparison['only_in_screen1']['tickers']) > 10:
                click.echo(f"  ... and {len(comparison['only_in_screen1']['tickers']) - 10} more\n")
        else:
            click.echo()

        click.echo(f"Only in {name2}: {comparison['only_in_screen2']['count']} stocks")
        if comparison['only_in_screen2']['tickers']:
            click.echo(f"  {', '.join(comparison['only_in_screen2']['tickers'][:10])}")
            if len(comparison['only_in_screen2']['tickers']) > 10:
                click.echo(f"  ... and {len(comparison['only_in_screen2']['tickers']) - 10} more")
        click.echo()

        # Save if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(comparison, f, indent=2)

            click.echo(f"✅ Comparison saved to: {output_path}")

    except Exception as e:
        click.echo(f"❌ Comparison failed: {e}", err=True)


def _get_screener(ctx) -> StockScreener:
    """Get initialized screener from context"""
    config = ctx.obj['config']
    db = ctx.obj['db']
    data_manager = ctx.obj['data_mgr']
    parquet = ctx.obj['parquet']

    return StockScreener(config, db, data_manager, parquet)


@screen.command('export')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['excel', 'csv', 'report']), default='excel',
              help='Export format (default: excel)')
@click.option('--output', type=click.Path(), required=True, help='Output file path')
@click.option('--enrich/--no-enrich', default=True, help='Add sector/industry data (default: yes)')
@click.pass_context
def screen_export(ctx, input_file, format, output, enrich):
    """
    Export screening results to Excel/CSV with enriched data

    Takes a JSON screen result file and exports it with:
    - Sector/industry classification
    - Company names
    - Calculated fields (% from SMA, BB position, etc.)
    - Rich formatting (Excel only)

    Examples:

      # Export to Excel with all enrichments
      quantlab screen export results/oversold.json --output results/oversold.xlsx

      # Export to CSV
      quantlab screen export results/value.json --format csv --output results/value.csv

      # Create multi-sheet report
      quantlab screen export results/growth.json --format report --output results/growth_report.xlsx
    """
    try:
        # Load results
        with open(input_file, 'r') as f:
            data = json.load(f)
            results_df = pd.DataFrame(data.get('results', []))

        if results_df.empty:
            click.echo("⚠️  No results to export")
            return

        # Get exporter
        from ..core.screen_export import ScreenExporter
        db = ctx.obj['db']
        lookup = ctx.obj['lookup']

        exporter = ScreenExporter(db, lookup)

        # Export based on format
        if format == 'excel':
            exporter.export_to_excel(results_df, output, enrich=enrich)
            click.echo(f"✅ Exported {len(results_df)} results to Excel: {output}")

        elif format == 'csv':
            exporter.export_to_csv(results_df, output, enrich=enrich)
            click.echo(f"✅ Exported {len(results_df)} results to CSV: {output}")

        elif format == 'report':
            exporter.create_comparison_report(results_df, output)
            click.echo(f"✅ Created analysis report: {output}")

    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


@screen.command('watch')
@click.argument('action', type=click.Choice(['create', 'list', 'show', 'save', 'delete', 'compare']))
@click.option('--id', 'watchlist_id', help='Watchlist ID')
@click.option('--name', help='Watchlist name (for create)')
@click.option('--description', help='Watchlist description')
@click.option('--input', 'input_file', type=click.Path(exists=True), help='Screen results JSON file to save')
@click.option('--merge', is_flag=True, help='Merge with existing items (default: replace)')
@click.option('--output', type=click.Path(), help='Output file path')
@click.pass_context
def watch_manage(ctx, action, watchlist_id, name, description, input_file, merge, output):
    """
    Manage watchlists from screening results

    Actions:
      create   - Create a new watchlist
      list     - List all watchlists
      show     - Show watchlist contents
      save     - Save screen results to watchlist
      delete   - Delete a watchlist
      compare  - Compare watchlist snapshots

    Examples:

      # Create a new watchlist
      quantlab screen watch create --id tech_watch --name "Tech Stocks" \\
          --description "Technology sector watchlist"

      # Save screening results to watchlist
      quantlab screen watch save --id tech_watch --input results/tech.json

      # List all watchlists
      quantlab screen watch list

      # Show watchlist contents
      quantlab screen watch show --id tech_watch

      # Compare snapshots over time
      quantlab screen watch compare --id tech_watch

      # Delete watchlist
      quantlab screen watch delete --id tech_watch
    """
    try:
        from ..core.watchlist import WatchlistManager
        db = ctx.obj['db']
        watchlist_mgr = WatchlistManager(db)

        if action == 'create':
            if not watchlist_id or not name:
                click.echo("❌ --id and --name are required for create")
                return

            success = watchlist_mgr.create_watchlist(
                watchlist_id=watchlist_id,
                name=name,
                description=description
            )

            if success:
                click.echo(f"✅ Created watchlist: {watchlist_id} ({name})")
            else:
                click.echo(f"❌ Failed to create watchlist")

        elif action == 'list':
            watchlists = watchlist_mgr.list_watchlists()

            if watchlists.empty:
                click.echo("📋 No watchlists found\n")
                click.echo("💡 Create one with: quantlab screen watch create --id my_watch --name \"My Watchlist\"")
                return

            click.echo(f"\n📋 Watchlists ({len(watchlists)}):\n")
            click.echo(tabulate(
                watchlists[['id', 'name', 'num_stocks', 'last_updated']],
                headers=['ID', 'Name', '# Stocks', 'Last Updated'],
                tablefmt='simple'
            ))
            click.echo()

        elif action == 'show':
            if not watchlist_id:
                click.echo("❌ --id is required for show")
                return

            items = watchlist_mgr.get_watchlist(watchlist_id)

            if items is None or items.empty:
                click.echo(f"⚠️  Watchlist '{watchlist_id}' is empty or not found")
                return

            click.echo(f"\n📊 Watchlist: {watchlist_id} ({len(items)} stocks)\n")
            click.echo(tabulate(
                items,
                headers='keys',
                tablefmt='simple'
            ))
            click.echo()

        elif action == 'save':
            if not watchlist_id or not input_file:
                click.echo("❌ --id and --input are required for save")
                return

            # Load screen results
            with open(input_file, 'r') as f:
                data = json.load(f)
                results_df = pd.DataFrame(data.get('results', []))

            if results_df.empty:
                click.echo("⚠️  No results to save")
                return

            # Save to watchlist
            count = watchlist_mgr.add_from_screen_results(
                watchlist_id=watchlist_id,
                screen_results=results_df,
                reason=f"Screen: {data.get('screen_name', 'Unknown')}",
                merge=merge
            )

            if count > 0:
                click.echo(f"✅ Added {count} stocks to watchlist: {watchlist_id}")
            else:
                click.echo("❌ Failed to add stocks to watchlist")

        elif action == 'delete':
            if not watchlist_id:
                click.echo("❌ --id is required for delete")
                return

            # Confirm deletion
            if not click.confirm(f"Are you sure you want to delete watchlist '{watchlist_id}'?"):
                click.echo("Cancelled")
                return

            success = watchlist_mgr.delete_watchlist(watchlist_id)

            if success:
                click.echo(f"✅ Deleted watchlist: {watchlist_id}")
            else:
                click.echo("❌ Failed to delete watchlist")

        elif action == 'compare':
            if not watchlist_id:
                click.echo("❌ --id is required for compare")
                return

            comparison = watchlist_mgr.compare_snapshots(watchlist_id)

            if not comparison:
                click.echo("⚠️  Not enough snapshots to compare (need at least 2)")
                return

            click.echo(f"\n📊 Watchlist Snapshot Comparison: {watchlist_id}\n")
            click.echo(f"From: {comparison['date1']}")
            click.echo(f"To:   {comparison['date2']}\n")

            click.echo(f"Added:     {len(comparison['added'])} stocks")
            if comparison['added']:
                click.echo(f"           {', '.join(comparison['added'][:10])}")
                if len(comparison['added']) > 10:
                    click.echo(f"           ... and {len(comparison['added']) - 10} more\n")

            click.echo(f"Removed:   {len(comparison['removed'])} stocks")
            if comparison['removed']:
                click.echo(f"           {', '.join(comparison['removed'][:10])}")
                if len(comparison['removed']) > 10:
                    click.echo(f"           ... and {len(comparison['removed']) - 10} more\n")

            click.echo(f"Unchanged: {len(comparison['unchanged'])} stocks\n")

            # Show price changes
            if comparison['price_changes']:
                click.echo("Top Price Changes:")
                sorted_changes = sorted(
                    comparison['price_changes'].items(),
                    key=lambda x: abs(x[1]['change_pct']),
                    reverse=True
                )[:10]

                for ticker, change in sorted_changes:
                    sign = "+" if change['change_pct'] > 0 else ""
                    click.echo(f"  {ticker}: ${change['old']:.2f} → ${change['new']:.2f} ({sign}{change['change_pct']:.1f}%)")

            click.echo()

    except Exception as e:
        click.echo(f"❌ Watchlist operation failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


@screen.command('saved')
@click.argument('action', type=click.Choice(['save', 'list', 'load', 'run', 'delete', 'export', 'import']))
@click.option('--id', 'screen_id', help='Screen ID')
@click.option('--name', help='Screen name (for save)')
@click.option('--description', help='Screen description')
@click.option('--tags', multiple=True, help='Tags for categorization (can specify multiple)')
@click.option('--file', 'file_path', type=click.Path(), help='File path for export/import')
@click.option('--limit', default=50, help='Limit for run action')
@click.option('--output', type=click.Path(), help='Output file for results')
# Screen criteria options (for save action)
@click.option('--rsi-min', type=float, help='Minimum RSI')
@click.option('--rsi-max', type=float, help='Maximum RSI')
@click.option('--macd-signal', type=click.Choice(['bullish', 'bearish']), help='MACD signal')
@click.option('--pe-max', type=float, help='Maximum P/E ratio')
@click.option('--revenue-growth-min', type=float, help='Minimum revenue growth %')
@click.option('--volume-min', type=int, help='Minimum volume')
@click.option('--sectors', multiple=True, help='Sectors to include')
@click.pass_context
def saved_screens(ctx, action, screen_id, name, description, tags, file_path, limit, output,
                  rsi_min, rsi_max, macd_signal, pe_max, revenue_growth_min, volume_min, sectors):
    """
    Manage saved screening criteria

    Actions:
      save    - Save screening criteria as a template
      list    - List all saved screens
      load    - Load a saved screen (show criteria)
      run     - Run a saved screen
      delete  - Delete a saved screen
      export  - Export screen to JSON file
      import  - Import screen from JSON file

    Examples:

      # Save a custom oversold screen
      quantlab screen saved save --id my_oversold \\
          --name "My Oversold Strategy" \\
          --description "RSI < 30 with high volume" \\
          --rsi-max 30 --volume-min 1000000 \\
          --tags oversold --tags technical

      # List all saved screens
      quantlab screen saved list

      # Run a saved screen
      quantlab screen saved run --id my_oversold --limit 20 --output results/oversold.json

      # Export screen for sharing
      quantlab screen saved export --id my_oversold --file my_screen.json

      # Import screen from file
      quantlab screen saved import --file friend_screen.json
    """
    try:
        from ..core.saved_screens import SavedScreenManager
        db = ctx.obj['db']
        saved_mgr = SavedScreenManager(db)

        if action == 'save':
            if not screen_id or not name:
                click.echo("❌ --id and --name are required for save")
                return

            # Create criteria from provided options
            criteria = ScreenCriteria(
                rsi_min=rsi_min,
                rsi_max=rsi_max,
                macd_signal=macd_signal,
                pe_max=pe_max,
                revenue_growth_min=revenue_growth_min,
                volume_min=volume_min,
                sectors=list(sectors) if sectors else None
            )

            success = saved_mgr.save_screen(
                screen_id=screen_id,
                name=name,
                criteria=criteria,
                description=description,
                tags=list(tags) if tags else None
            )

            if success:
                click.echo(f"✅ Saved screen: {screen_id} ({name})")
            else:
                click.echo("❌ Failed to save screen")

        elif action == 'list':
            screens = saved_mgr.list_screens()

            if screens.empty:
                click.echo("📋 No saved screens found\n")
                click.echo("💡 Save a screen with: quantlab screen saved save --id my_screen --name \"My Screen\" --rsi-max 30")
                return

            click.echo(f"\n📋 Saved Screens ({len(screens)}):\n")

            # Format for display
            display_df = screens[['id', 'name', 'run_count', 'last_modified']].copy()
            display_df['last_modified'] = pd.to_datetime(display_df['last_modified']).dt.strftime('%Y-%m-%d %H:%M')

            click.echo(tabulate(
                display_df,
                headers=['ID', 'Name', 'Runs', 'Last Modified'],
                tablefmt='simple',
                showindex=False
            ))
            click.echo()

        elif action == 'load':
            if not screen_id:
                click.echo("❌ --id is required for load")
                return

            info = saved_mgr.get_screen_info(screen_id)

            if not info:
                click.echo(f"❌ Screen not found: {screen_id}")
                return

            click.echo(f"\n📊 Saved Screen: {info['id']}\n")
            click.echo(f"Name: {info['name']}")
            if info['description']:
                click.echo(f"Description: {info['description']}")
            if info['tags']:
                click.echo(f"Tags: {', '.join(info['tags'])}")
            click.echo(f"Created: {info['created_date']}")
            click.echo(f"Last Modified: {info['last_modified']}")
            click.echo(f"Times Run: {info['run_count']}")
            click.echo(f"\nCriteria:")

            # Display criteria
            criteria = info['criteria']
            for key, value in criteria.items():
                if value is not None:
                    click.echo(f"  {key}: {value}")
            click.echo()

        elif action == 'run':
            if not screen_id:
                click.echo("❌ --id is required for run")
                return

            criteria = saved_mgr.load_screen(screen_id)

            if not criteria:
                click.echo(f"❌ Screen not found: {screen_id}")
                return

            # Run the screen
            screener = _get_screener(ctx)
            screen_info = saved_mgr.get_screen_info(screen_id)
            click.echo(f"\n🔍 Running saved screen: {screen_info['name']}\n")

            results = screener.screen(criteria, limit=limit, include_score=True)

            # Update run stats
            saved_mgr.update_run_stats(screen_id)

            # Display results
            _display_results(results, output, screen_info['name'])

        elif action == 'delete':
            if not screen_id:
                click.echo("❌ --id is required for delete")
                return

            # Confirm deletion
            if not click.confirm(f"Are you sure you want to delete screen '{screen_id}'?"):
                click.echo("Cancelled")
                return

            success = saved_mgr.delete_screen(screen_id)

            if success:
                click.echo(f"✅ Deleted screen: {screen_id}")
            else:
                click.echo("❌ Failed to delete screen")

        elif action == 'export':
            if not screen_id or not file_path:
                click.echo("❌ --id and --file are required for export")
                return

            success = saved_mgr.export_screen(screen_id, file_path)

            if success:
                click.echo(f"✅ Exported screen {screen_id} to: {file_path}")
            else:
                click.echo("❌ Failed to export screen")

        elif action == 'import':
            if not file_path:
                click.echo("❌ --file is required for import")
                return

            success = saved_mgr.import_screen(file_path, screen_id)

            if success:
                click.echo(f"✅ Imported screen from: {file_path}")
            else:
                click.echo("❌ Failed to import screen")

    except Exception as e:
        click.echo(f"❌ Saved screen operation failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


@screen.command('backtest')
@click.option('--saved-id', help='ID of saved screen to backtest')
@click.option('--rsi-max', type=float, help='Maximum RSI for custom criteria')
@click.option('--volume-min', type=int, help='Minimum volume for custom criteria')
@click.option('--start-date', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='End date (YYYY-MM-DD)')
@click.option('--frequency', type=click.Choice(['daily', 'weekly', 'monthly']), default='weekly')
@click.option('--output', type=click.Path(), help='Save backtest report to JSON')
@click.pass_context
def backtest_screen(ctx, saved_id, rsi_max, volume_min, start_date, end_date, frequency, output):
    """
    Backtest screening criteria over historical period

    Examples:
      # Backtest saved screen
      quantlab screen backtest --saved-id my_oversold \\
          --start-date 2025-04-01 --end-date 2025-10-01

      # Backtest custom criteria
      quantlab screen backtest --rsi-max 30 --volume-min 1000000 \\
          --start-date 2025-01-01 --end-date 2025-10-01 --frequency weekly
    """
    try:
        from datetime import datetime
        from ..core.screen_backtest import ScreenBacktester

        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Get criteria
        if saved_id:
            from ..core.saved_screens import SavedScreenManager
            saved_mgr = SavedScreenManager(ctx.obj['db'])
            criteria = saved_mgr.load_screen(saved_id)
            if not criteria:
                click.echo(f"❌ Screen not found: {saved_id}")
                return
            screen_name = saved_mgr.get_screen_info(saved_id)['name']
        else:
            criteria = ScreenCriteria(rsi_max=rsi_max, volume_min=volume_min)
            screen_name = "Custom Screen"

        # Run backtest
        screener = _get_screener(ctx)
        backtester = ScreenBacktester(ctx.obj['db'], ctx.obj['parquet'], screener)

        click.echo(f"\n🔍 Backtesting: {screen_name}")
        click.echo(f"   Period: {start_date} to {end_date}")
        click.echo(f"   Frequency: {frequency}\n")

        backtest = backtester.backtest_criteria(criteria, start, end, frequency)

        # Display results
        click.echo("\n📊 Backtest Results:\n")
        click.echo(f"Total Periods: {backtest.total_periods}")
        click.echo(f"Avg Stocks/Period: {backtest.avg_stocks_per_period:.1f}")
        click.echo(f"\nPerformance:")
        click.echo(f"  Total Return: {backtest.total_return:.2f}%")
        click.echo(f"  Annualized Return: {backtest.annualized_return:.2f}%")
        click.echo(f"  Sharpe Ratio: {backtest.sharpe_ratio:.2f}")
        click.echo(f"  Max Drawdown: {backtest.max_drawdown:.2f}%")
        click.echo(f"  Win Rate: {backtest.win_rate:.1f}%")

        if backtest.benchmark_return:
            click.echo(f"\nBenchmark Comparison:")
            click.echo(f"  SPY Return: {backtest.benchmark_return:.2f}%")
            if backtest.alpha:
                click.echo(f"  Alpha: {backtest.alpha:.2f}%")

        # Save report
        if output:
            backtester.export_backtest_report(backtest, output)
            click.echo(f"\n✅ Report saved to: {output}")

        click.echo()

    except Exception as e:
        click.echo(f"❌ Backtest failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


@screen.command('compare-multi')
@click.option('--saved', 'saved_ids', multiple=True, help='Saved screen IDs to compare (can specify multiple)')
@click.option('--preset', 'presets', multiple=True,
              type=click.Choice(['value-stocks', 'growth-stocks', 'oversold', 'overbought', 'momentum', 'quality']),
              help='Preset strategies to compare')
@click.option('--limit', default=50, help='Max results per screen (default: 50)')
@click.option('--output', type=click.Path(), help='Save comparison report (Excel or JSON)')
@click.option('--format', type=click.Choice(['excel', 'json']), default='excel', help='Output format')
@click.pass_context
def compare_multi_screens(ctx, saved_ids, presets, limit, output, format):
    """
    Compare multiple screening strategies side-by-side

    Analyzes overlaps, finds consensus picks (stocks in multiple screens),
    and provides comprehensive comparison metrics.

    Examples:

      # Compare multiple saved screens
      quantlab screen compare-multi \\
          --saved my_oversold \\
          --saved my_momentum \\
          --saved my_value

      # Compare preset strategies
      quantlab screen compare-multi \\
          --preset value-stocks \\
          --preset growth-stocks \\
          --preset quality

      # Mix saved and presets
      quantlab screen compare-multi \\
          --saved my_custom \\
          --preset oversold \\
          --preset momentum \\
          --output comparison.xlsx
    """
    try:
        from ..core.screen_comparison import ScreenComparator
        from ..core.saved_screens import SavedScreenManager

        screener = _get_screener(ctx)
        comparator = ScreenComparator(screener)

        # Build screens dictionary
        screens = {}

        # Load saved screens
        if saved_ids:
            saved_mgr = SavedScreenManager(ctx.obj['db'])
            for screen_id in saved_ids:
                criteria = saved_mgr.load_screen(screen_id)
                if not criteria:
                    click.echo(f"⚠️  Screen not found: {screen_id}, skipping...")
                    continue
                info = saved_mgr.get_screen_info(screen_id)
                screens[info['name']] = criteria

        # Add presets
        if presets:
            preset_definitions = {
                'value-stocks': ScreenCriteria(
                    pe_max=15,
                    debt_equity_max=1.5,
                    revenue_growth_min=5,
                    profit_margin_min=10,
                    volume_min=500000
                ),
                'growth-stocks': ScreenCriteria(
                    revenue_growth_min=20,
                    profit_margin_min=15,
                    market_cap_min=1.0,
                    volume_min=1000000
                ),
                'oversold': ScreenCriteria(
                    rsi_max=30,
                    volume_min=1000000,
                    price_min=5.0
                ),
                'overbought': ScreenCriteria(
                    rsi_min=70,
                    volume_min=1000000,
                    price_min=5.0
                ),
                'momentum': ScreenCriteria(
                    macd_signal='bullish',
                    adx_min=25,
                    volume_min=1000000,
                    price_above_sma50=True
                ),
                'quality': ScreenCriteria(
                    profit_margin_min=20,
                    debt_equity_max=1.0,
                    revenue_growth_min=10,
                    roe_min=15
                )
            }

            for preset in presets:
                screens[preset.replace('-', ' ').title()] = preset_definitions[preset]

        if not screens:
            click.echo("❌ No valid screens to compare")
            click.echo("💡 Specify at least 2 screens with --saved or --preset")
            return

        if len(screens) < 2:
            click.echo("❌ Need at least 2 screens to compare")
            return

        # Run comparison
        click.echo(f"\n🔍 Comparing {len(screens)} screening strategies...\n")

        comparison = comparator.compare_screens(screens, limit_per_screen=limit, include_scores=True)

        # Display results
        click.echo("\n📊 Comparison Summary:\n")
        click.echo(tabulate(
            comparison.comparison_metrics,
            headers='keys',
            tablefmt='simple',
            showindex=False,
            floatfmt='.2f'
        ))

        click.echo("\n📈 Overlap Analysis:\n")
        click.echo(tabulate(
            comparison.overlap_analysis,
            headers='keys',
            tablefmt='simple',
            showindex=False
        ))

        if not comparison.consensus_picks.empty:
            click.echo(f"\n⭐ Consensus Picks ({len(comparison.consensus_picks)} stocks found in multiple screens):\n")

            # Show top 15 consensus picks
            display_cols = ['ticker', 'appearances', 'screens', 'price']
            if 'avg_score' in comparison.consensus_picks.columns:
                display_cols.insert(2, 'avg_score')

            display_df = comparison.consensus_picks[display_cols].head(15).copy()

            # Format for display
            if 'price' in display_df.columns:
                display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
            if 'avg_score' in display_df.columns:
                display_df['avg_score'] = display_df['avg_score'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")

            click.echo(tabulate(
                display_df,
                headers=['Ticker', 'Screens', 'Avg Score', 'In Strategies', 'Price'] if 'avg_score' in display_cols
                        else ['Ticker', 'Screens', 'In Strategies', 'Price'],
                tablefmt='simple',
                showindex=False
            ))

            if len(comparison.consensus_picks) > 15:
                click.echo(f"\n... {len(comparison.consensus_picks) - 15} more consensus picks")

        # Save report
        if output:
            if format == 'excel':
                comparator.export_comparison_report(comparison, output)
                click.echo(f"\n✅ Comparison report saved to: {output}")
            else:
                comparator.export_comparison_json(comparison, output)
                click.echo(f"\n✅ Comparison JSON saved to: {output}")

        click.echo()

    except Exception as e:
        click.echo(f"❌ Comparison failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


@screen.command('watch-monitor')
@click.argument('action', type=click.Choice(['start', 'stop', 'list', 'run-cycle', 'alerts']))
@click.option('--screen-id', help='Saved screen ID to monitor')
@click.option('--session-id', help='Watch session ID (for stop/alerts actions)')
@click.option('--interval', default='1h', help='Check interval: 15m, 1h, 4h, 1d (default: 1h)')
@click.option('--alert-on', multiple=True,
              type=click.Choice(['entry', 'exit', 'price_change', 'volume_spike']),
              help='Alert types (can specify multiple)')
@click.option('--since-hours', type=int, help='Show alerts from last N hours')
@click.option('--unack-only', is_flag=True, help='Show only unacknowledged alerts')
@click.pass_context
def watch_monitor(ctx, action, screen_id, session_id, interval, alert_on, since_hours, unack_only):
    """
    Monitor saved screens with real-time alerts

    Actions:
      start      - Start monitoring a saved screen
      stop       - Stop a watch session
      list       - List active watch sessions
      run-cycle  - Manually run one watch cycle (checks all active sessions)
      alerts     - View alerts from watch sessions

    Examples:

      # Start monitoring oversold screen (check every hour)
      quantlab screen watch-monitor start --screen-id my_oversold --interval 1h

      # Start with specific alerts
      quantlab screen watch-monitor start --screen-id my_momentum \\
          --interval 15m \\
          --alert-on entry --alert-on exit --alert-on price_change

      # List active sessions
      quantlab screen watch-monitor list

      # Run one watch cycle manually
      quantlab screen watch-monitor run-cycle

      # View recent alerts (last 24 hours)
      quantlab screen watch-monitor alerts --since-hours 24

      # View unacknowledged alerts only
      quantlab screen watch-monitor alerts --unack-only

      # Stop a watch session
      quantlab screen watch-monitor stop --session-id my_oversold_20251016_120000
    """
    try:
        from ..core.screen_watcher import ScreenWatcher
        from ..core.saved_screens import SavedScreenManager
        from datetime import datetime, timedelta

        db = ctx.obj['db']
        saved_mgr = SavedScreenManager(db)
        screener = _get_screener(ctx)
        watcher = ScreenWatcher(db, screener, saved_mgr)

        if action == 'start':
            if not screen_id:
                click.echo("❌ --screen-id is required for start")
                return

            alert_types = list(alert_on) if alert_on else None

            session_id_result = watcher.start_watch(
                screen_id=screen_id,
                interval=interval,
                alert_on=alert_types
            )

            if session_id_result:
                click.echo(f"✅ Started watch session: {session_id_result}")
                click.echo(f"   Screen: {screen_id}")
                click.echo(f"   Interval: {interval}")
                if alert_types:
                    click.echo(f"   Alerts: {', '.join(alert_types)}")
                click.echo()
                click.echo("💡 Use 'quantlab screen watch-monitor run-cycle' to manually check")
                click.echo("   or set up a cron job to run this command periodically")
            else:
                click.echo("❌ Failed to start watch session")

        elif action == 'stop':
            if not session_id:
                click.echo("❌ --session-id is required for stop")
                return

            success = watcher.stop_watch(session_id)

            if success:
                click.echo(f"✅ Stopped watch session: {session_id}")
            else:
                click.echo("❌ Failed to stop watch session")

        elif action == 'list':
            sessions = watcher.get_active_watches()

            if sessions.empty:
                click.echo("📋 No active watch sessions\n")
                click.echo("💡 Start one with: quantlab screen watch-monitor start --screen-id my_screen")
                return

            click.echo(f"\n📋 Active Watch Sessions ({len(sessions)}):\n")

            # Format for display
            display_df = sessions[['session_id', 'screen_name', 'interval', 'alerts', 'runs', 'next_run']].copy()
            display_df['next_run'] = pd.to_datetime(display_df['next_run']).dt.strftime('%Y-%m-%d %H:%M')

            click.echo(tabulate(
                display_df,
                headers=['Session ID', 'Screen', 'Interval', 'Alerts', 'Runs', 'Next Run'],
                tablefmt='simple',
                showindex=False
            ))
            click.echo()

        elif action == 'run-cycle':
            click.echo("\n🔍 Running watch cycle...\n")

            sessions_checked = watcher.run_watch_cycle()

            if sessions_checked > 0:
                click.echo(f"✅ Checked {sessions_checked} watch sessions")

                # Show any new alerts
                since = datetime.now() - timedelta(minutes=5)
                recent_alerts = watcher.get_alerts(since=since, unacknowledged_only=True)

                if not recent_alerts.empty:
                    click.echo(f"\n⚠️  {len(recent_alerts)} new alerts:\n")
                    display_df = recent_alerts[['ticker', 'alert_type', 'message']].head(10)
                    click.echo(tabulate(
                        display_df,
                        headers=['Ticker', 'Type', 'Message'],
                        tablefmt='simple',
                        showindex=False
                    ))
                    if len(recent_alerts) > 10:
                        click.echo(f"\n... {len(recent_alerts) - 10} more alerts")
            else:
                click.echo("📋 No sessions due for checking")

            click.echo()

        elif action == 'alerts':
            since = None
            if since_hours:
                since = datetime.now() - timedelta(hours=since_hours)

            alerts = watcher.get_alerts(
                session_id=session_id,
                since=since,
                unacknowledged_only=unack_only
            )

            if alerts.empty:
                click.echo("📋 No alerts found\n")
                return

            click.echo(f"\n🔔 Alerts ({len(alerts)}):\n")

            # Format for display
            display_df = alerts[['alert_time', 'screen_name', 'ticker', 'alert_type', 'message']].head(50).copy()
            display_df['alert_time'] = pd.to_datetime(display_df['alert_time']).dt.strftime('%Y-%m-%d %H:%M')

            click.echo(tabulate(
                display_df,
                headers=['Time', 'Screen', 'Ticker', 'Type', 'Message'],
                tablefmt='simple',
                showindex=False
            ))

            if len(alerts) > 50:
                click.echo(f"\n... {len(alerts) - 50} more alerts")

            # Show unacknowledged count
            unack_count = (~alerts['acknowledged']).sum()
            if unack_count > 0:
                click.echo(f"\n💡 {unack_count} unacknowledged alerts")

            click.echo()

    except Exception as e:
        click.echo(f"❌ Watch operation failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


def _display_results(results, output_path, screen_name):
    """Display screening results and optionally save to file"""

    if results.empty:
        click.echo("⚠️  No stocks matched the criteria\n")
        click.echo("💡 Try relaxing some filters or using a different preset")
        return

    click.echo(f"✅ Found {len(results)} matching stocks\n")

    # Determine columns to display
    display_cols = ['ticker', 'price']

    # Add available columns based on what's in results
    if 'rsi' in results.columns:
        display_cols.append('rsi')
    if 'macd_histogram' in results.columns:
        display_cols.append('macd_histogram')
    if 'pe_ratio' in results.columns:
        display_cols.append('pe_ratio')
    if 'revenue_growth' in results.columns:
        display_cols.append('revenue_growth')
    if 'profit_margin' in results.columns:
        display_cols.append('profit_margin')
    if 'sentiment_score' in results.columns:
        display_cols.append('sentiment_score')
    if 'score' in results.columns:
        display_cols.append('score')

    # Filter to available columns
    available_cols = [col for col in display_cols if col in results.columns]
    display_df = results[available_cols].copy()

    # Format numbers for display
    if 'price' in display_df.columns:
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
    if 'rsi' in display_df.columns:
        display_df['rsi'] = display_df['rsi'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    if 'macd_histogram' in display_df.columns:
        display_df['macd_histogram'] = display_df['macd_histogram'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "-")
    if 'pe_ratio' in display_df.columns:
        display_df['pe_ratio'] = display_df['pe_ratio'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    if 'revenue_growth' in display_df.columns:
        display_df['revenue_growth'] = display_df['revenue_growth'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    if 'profit_margin' in display_df.columns:
        display_df['profit_margin'] = display_df['profit_margin'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    if 'sentiment_score' in display_df.columns:
        display_df['sentiment_score'] = display_df['sentiment_score'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    if 'score' in display_df.columns:
        display_df['score'] = display_df['score'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")

    # Display table
    click.echo(f"📊 {screen_name} Results:\n")
    click.echo(tabulate(display_df.head(20), headers='keys', tablefmt='simple', showindex=False))

    if len(display_df) > 20:
        click.echo(f"\n... {len(display_df) - 20} more results")

    # Save to file if requested
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable format
        results_dict = results.to_dict('records')

        with open(output_path, 'w') as f:
            json.dump({
                'screen_name': screen_name,
                'num_results': len(results),
                'results': results_dict
            }, f, indent=2, default=str)

        click.echo(f"\n✅ Results saved to: {output_path}")

    click.echo()
