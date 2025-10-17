"""
Main Orchestrator for Profitable Small-Cap AI Stock Analysis

Runs complete analysis pipeline:
1. Screen for profitable small-cap AI stocks
2. Perform sentiment analysis
3. Conduct technical analysis and generate strategies
4. Create comprehensive report
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from screener import OptimizedAIScreener
from sentiment_analysis import SentimentAnalyzer
from technical_analysis import TechnicalAnalyzer


class AnalysisPipeline:
    """Complete analysis pipeline"""

    def __init__(self, min_cap=300_000_000, max_cap=5_000_000_000):
        self.min_cap = min_cap
        self.max_cap = max_cap
        self.output_dir = Path(__file__).parent / "data"
        self.output_dir.mkdir(exist_ok=True)

    def run_complete_analysis(self):
        """Run the complete analysis pipeline"""
        print("\n" + "="*80)
        print("PROFITABLE SMALL-CAP AI STOCK ANALYSIS PIPELINE")
        print("="*80)
        print(f"Market Cap Range: ${self.min_cap/1e6:.0f}M - ${self.max_cap/1e9:.1f}B")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # Step 1: Screen for stocks
        print("\n" + "="*80)
        print("STEP 1: SCREENING FOR PROFITABLE SMALL-CAP AI STOCKS")
        print("="*80)

        screener = OptimizedAIScreener(
            min_cap=self.min_cap,
            max_cap=self.max_cap
        )

        df_screened = screener.screen(verbose=True)

        if df_screened.empty:
            print("\n❌ No stocks passed the screening criteria. Exiting.")
            return

        # Get summary stats
        stats = screener.get_summary_stats(df_screened)

        print("\n📊 Screening Summary:")
        print(f"   • Total stocks found: {stats['total_stocks']}")
        print(f"   • Average market cap: ${stats['avg_market_cap']/1e9:.2f}B")
        print(f"   • Average profit margin: {stats['avg_profit_margin']*100:.2f}%")

        # Export tickers for next steps
        screener.export_for_analysis(df_screened)

        tickers = df_screened['ticker'].tolist()

        # Step 2: Sentiment Analysis
        print("\n" + "="*80)
        print("STEP 2: SENTIMENT ANALYSIS")
        print("="*80)

        sentiment_analyzer = SentimentAnalyzer()
        df_sentiment = sentiment_analyzer.analyze_batch(tickers, days_back=30)

        if not df_sentiment.empty:
            sentiment_analyzer.print_sentiment_summary(df_sentiment)

        # Step 3: Technical Analysis
        print("\n" + "="*80)
        print("STEP 3: TECHNICAL ANALYSIS & STRATEGY GENERATION")
        print("="*80)

        technical_analyzer = TechnicalAnalyzer()
        technical_analyses = technical_analyzer.analyze_batch(tickers, period="1y")

        if technical_analyses:
            technical_analyzer.generate_strategy_report(technical_analyses)

        # Step 4: Generate Final Report
        print("\n" + "="*80)
        print("STEP 4: GENERATING COMPREHENSIVE REPORT")
        print("="*80)

        self._generate_final_report(df_screened, df_sentiment, technical_analyses)

        print("\n" + "="*80)
        print("✅ ANALYSIS PIPELINE COMPLETE")
        print("="*80)
        print(f"\nResults saved in: {self.output_dir}")
        print("\nNext steps:")
        print("  1. Review the comprehensive report")
        print("  2. Analyze individual stock strategies")
        print("  3. Monitor sentiment changes")
        print("  4. Execute trades based on your risk tolerance")
        print("="*80 + "\n")

    def _generate_final_report(self, df_screened, df_sentiment, technical_analyses):
        """Generate comprehensive final report"""

        # Merge all data
        final_data = []

        for _, stock in df_screened.iterrows():
            ticker = stock['ticker']

            # Get sentiment data
            sentiment_data = {}
            if not df_sentiment.empty and ticker in df_sentiment['ticker'].values:
                sentiment_row = df_sentiment[df_sentiment['ticker'] == ticker].iloc[0]
                sentiment_data = {
                    'sentiment_score': sentiment_row.get('sentiment_score', 0),
                    'sentiment': sentiment_row.get('sentiment', 'Neutral'),
                    'news_count': sentiment_row.get('news_count', 0)
                }

            # Get technical data
            technical_data = {}
            for analysis in technical_analyses:
                if analysis['ticker'] == ticker:
                    technical_data = {
                        'trend': analysis.get('trend', 'Unknown'),
                        'rsi': analysis['indicators'].get('rsi'),
                        'strategies_count': len(analysis.get('strategies', []))
                    }
                    break

            # Combine all data
            combined = {
                'ticker': ticker,
                'name': stock['name'],
                'market_cap': stock['market_cap'],
                'current_price': stock['current_price'],
                'profit_margin': stock['profit_margin'],
                'pe_ratio': stock['pe_ratio'],
                'revenue_growth': stock['revenue_growth'],
                'industry': stock['industry'],

                **sentiment_data,
                **technical_data
            }

            final_data.append(combined)

        # Create comprehensive report
        report = {
            'report_date': datetime.now().isoformat(),
            'analysis_summary': {
                'total_stocks_analyzed': len(df_screened),
                'market_cap_range': {
                    'min': self.min_cap,
                    'max': self.max_cap
                },
                'avg_profit_margin': df_screened['profit_margin'].mean() if 'profit_margin' in df_screened.columns else None,
                'sentiment_distribution': df_sentiment['sentiment'].value_counts().to_dict() if not df_sentiment.empty else {}
            },
            'stocks': final_data
        }

        # Save report
        report_file = self.output_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Comprehensive report saved to: {report_file}")

        # Print top opportunities
        self._print_top_opportunities(final_data)

    def _print_top_opportunities(self, final_data):
        """Print top trading opportunities"""
        print("\n" + "="*80)
        print("🎯 TOP TRADING OPPORTUNITIES")
        print("="*80)

        # Score each stock based on multiple factors
        for stock in final_data:
            score = 0

            # Fundamental score
            if stock.get('profit_margin') and stock['profit_margin'] > 0.1:
                score += 2
            if stock.get('revenue_growth') and stock['revenue_growth'] > 0.15:
                score += 2
            if stock.get('pe_ratio') and stock['pe_ratio'] < 30:
                score += 1

            # Sentiment score
            sentiment = stock.get('sentiment', 'Neutral')
            if sentiment == 'Bullish':
                score += 3
            elif sentiment == 'Bearish':
                score -= 2

            # Technical score
            trend = stock.get('trend', '')
            if 'Uptrend' in trend:
                score += 2
            elif 'Downtrend' in trend:
                score -= 1

            rsi = stock.get('rsi')
            if rsi:
                if 30 <= rsi <= 50:
                    score += 2  # Oversold to neutral
                elif rsi < 30:
                    score += 1  # Oversold

            stock['opportunity_score'] = score

        # Sort by score
        final_data.sort(key=lambda x: x['opportunity_score'], reverse=True)

        # Print top 5
        print("\nTop 5 Opportunities (by combined score):\n")

        for i, stock in enumerate(final_data[:5], 1):
            cap_str = f"${stock['market_cap']/1e9:.2f}B" if stock['market_cap'] >= 1e9 else f"${stock['market_cap']/1e6:.0f}M"

            print(f"{i}. {stock['ticker']} - {stock['name'][:40]}")
            print(f"   Score: {stock['opportunity_score']}/10")
            print(f"   Market Cap: {cap_str} | Price: ${stock['current_price']:.2f}")

            if stock.get('profit_margin'):
                print(f"   Profit Margin: {stock['profit_margin']*100:.1f}%", end="")
            if stock.get('revenue_growth'):
                print(f" | Rev Growth: {stock['revenue_growth']*100:.1f}%", end="")
            print()

            if stock.get('sentiment'):
                print(f"   Sentiment: {stock['sentiment']}", end="")
            if stock.get('trend'):
                print(f" | Trend: {stock['trend']}", end="")
            print()

            if stock.get('rsi'):
                print(f"   RSI: {stock['rsi']:.1f}", end="")
            if stock.get('strategies_count'):
                print(f" | {stock['strategies_count']} strategies available", end="")
            print("\n")

        print("="*80)


def main():
    """Main execution"""
    pipeline = AnalysisPipeline(
        min_cap=300_000_000,    # $300M
        max_cap=5_000_000_000   # $5B
    )

    pipeline.run_complete_analysis()


if __name__ == "__main__":
    main()
