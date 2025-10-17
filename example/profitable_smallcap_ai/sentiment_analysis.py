"""
Sentiment Analysis for Profitable Small-Cap AI Stocks

Analyzes sentiment from:
1. News articles (Polygon API)
2. Social media mentions (if available)
3. Analyst ratings and price targets
"""

import os
import requests
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
from collections import Counter
import json

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class SentimentAnalyzer:
    """Analyze sentiment for stocks"""

    def __init__(self):
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)

    def get_news_sentiment(self, ticker: str, days_back: int = 30) -> Dict:
        """
        Get news sentiment for a ticker using Polygon News API

        Args:
            ticker: Stock ticker
            days_back: Number of days to look back

        Returns:
            Dictionary with sentiment analysis
        """
        if not self.polygon_api_key:
            print("Warning: Polygon API key not found")
            return {}

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        endpoint = "https://api.polygon.io/v2/reference/news"
        params = {
            'ticker': ticker,
            'published_utc.gte': start_date.strftime('%Y-%m-%d'),
            'published_utc.lte': end_date.strftime('%Y-%m-%d'),
            'limit': 100,
            'apiKey': self.polygon_api_key
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])

            if not results:
                return {
                    'ticker': ticker,
                    'news_count': 0,
                    'sentiment_score': 0,
                    'sentiment': 'Neutral',
                    'articles': []
                }

            # Analyze sentiment from article data
            sentiment_data = self._analyze_news_articles(results, ticker)
            sentiment_data['ticker'] = ticker
            sentiment_data['date_range'] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            return sentiment_data

        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return {}

    def _analyze_news_articles(self, articles: List[Dict], ticker: str) -> Dict:
        """
        Analyze sentiment from news articles

        Simple keyword-based sentiment analysis
        For production, consider using a proper NLP model
        """
        # Sentiment keywords
        positive_keywords = [
            'beat', 'beats', 'growth', 'surge', 'rally', 'gain', 'gains', 'up',
            'profit', 'bullish', 'upgrade', 'outperform', 'buy', 'strong',
            'positive', 'innovation', 'breakthrough', 'success', 'partnership',
            'acquisition', 'revenue', 'earnings', 'exceed', 'milestone',
            'leadership', 'expansion', 'launch', 'award'
        ]

        negative_keywords = [
            'loss', 'losses', 'decline', 'fall', 'drop', 'down', 'miss', 'misses',
            'bearish', 'downgrade', 'sell', 'weak', 'negative', 'concern',
            'risk', 'threat', 'investigation', 'lawsuit', 'layoff', 'cut',
            'warning', 'disappointing', 'struggle', 'challenge', 'crisis'
        ]

        sentiment_scores = []
        article_sentiments = []

        for article in articles:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            text = f"{title} {description}"

            # Count positive and negative keywords
            pos_count = sum(1 for word in positive_keywords if word in text)
            neg_count = sum(1 for word in negative_keywords if word in text)

            # Calculate sentiment score for this article
            if pos_count + neg_count > 0:
                score = (pos_count - neg_count) / (pos_count + neg_count)
            else:
                score = 0

            sentiment_scores.append(score)

            article_sentiments.append({
                'title': article.get('title', ''),
                'url': article.get('article_url', ''),
                'published': article.get('published_utc', ''),
                'publisher': article.get('publisher', {}).get('name', 'Unknown'),
                'sentiment_score': score,
                'sentiment': 'Positive' if score > 0.2 else 'Negative' if score < -0.2 else 'Neutral'
            })

        # Overall sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        # Determine overall sentiment category
        if avg_sentiment > 0.2:
            overall_sentiment = 'Bullish'
        elif avg_sentiment < -0.2:
            overall_sentiment = 'Bearish'
        else:
            overall_sentiment = 'Neutral'

        return {
            'news_count': len(articles),
            'sentiment_score': avg_sentiment,
            'sentiment': overall_sentiment,
            'positive_articles': sum(1 for s in sentiment_scores if s > 0.2),
            'negative_articles': sum(1 for s in sentiment_scores if s < -0.2),
            'neutral_articles': sum(1 for s in sentiment_scores if -0.2 <= s <= 0.2),
            'articles': article_sentiments[:10],  # Top 10 recent articles
            'timestamp': datetime.now().isoformat()
        }

    def analyze_batch(self, tickers: List[str], days_back: int = 30) -> pd.DataFrame:
        """
        Analyze sentiment for multiple tickers

        Args:
            tickers: List of stock tickers
            days_back: Days to look back for news

        Returns:
            DataFrame with sentiment analysis
        """
        print("\n" + "="*80)
        print("SENTIMENT ANALYSIS")
        print("="*80)
        print(f"Analyzing {len(tickers)} stocks")
        print(f"News period: Last {days_back} days")
        print("="*80 + "\n")

        results = []

        for ticker in tickers:
            print(f"Analyzing {ticker}...", end=" ")

            sentiment = self.get_news_sentiment(ticker, days_back)

            if sentiment and sentiment.get('news_count', 0) > 0:
                results.append(sentiment)
                print(f"✅ {sentiment['news_count']} articles | {sentiment['sentiment']}")
            else:
                print(f"❌ No news found")

        df = pd.DataFrame(results)

        if not df.empty:
            # Sort by sentiment score
            df = df.sort_values('sentiment_score', ascending=False)

            # Save results
            output_file = self.data_dir / f"sentiment_analysis_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False)

            # Save detailed report with articles
            detailed_report = {
                'analysis_date': datetime.now().isoformat(),
                'stocks_analyzed': len(df),
                'results': results
            }

            report_file = self.data_dir / f"sentiment_detailed_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(detailed_report, f, indent=2)

            print(f"\n✅ Sentiment analysis saved to: {output_file}")
            print(f"✅ Detailed report saved to: {report_file}")

        return df

    def print_sentiment_summary(self, df: pd.DataFrame):
        """Print sentiment analysis summary"""
        if df.empty:
            print("No sentiment data available")
            return

        print("\n" + "="*80)
        print("SENTIMENT SUMMARY")
        print("="*80)

        # Overall statistics
        total = len(df)
        bullish = len(df[df['sentiment'] == 'Bullish'])
        bearish = len(df[df['sentiment'] == 'Bearish'])
        neutral = len(df[df['sentiment'] == 'Neutral'])

        print(f"\nOverall Sentiment Distribution:")
        print(f"  🟢 Bullish: {bullish} ({bullish/total*100:.1f}%)")
        print(f"  🔴 Bearish: {bearish} ({bearish/total*100:.1f}%)")
        print(f"  ⚪ Neutral:  {neutral} ({neutral/total*100:.1f}%)")

        # Top bullish stocks
        print("\n📈 Most Bullish Stocks:")
        top_bullish = df.nlargest(5, 'sentiment_score')[['ticker', 'sentiment_score', 'news_count', 'sentiment']]
        for idx, row in top_bullish.iterrows():
            print(f"  {row['ticker']:6s} | Score: {row['sentiment_score']:+.3f} | {row['news_count']} articles")

        # Top bearish stocks
        print("\n📉 Most Bearish Stocks:")
        top_bearish = df.nsmallest(5, 'sentiment_score')[['ticker', 'sentiment_score', 'news_count', 'sentiment']]
        for idx, row in top_bearish.iterrows():
            print(f"  {row['ticker']:6s} | Score: {row['sentiment_score']:+.3f} | {row['news_count']} articles")

        # News coverage
        print(f"\n📰 News Coverage:")
        print(f"  Total articles analyzed: {df['news_count'].sum()}")
        print(f"  Average articles per stock: {df['news_count'].mean():.1f}")

        most_covered = df.nlargest(3, 'news_count')[['ticker', 'news_count']]
        print(f"  Most covered stocks:")
        for idx, row in most_covered.iterrows():
            print(f"    - {row['ticker']}: {row['news_count']} articles")

        print("="*80)


def main():
    """Run sentiment analysis"""
    analyzer = SentimentAnalyzer()

    # Load tickers from screener output
    data_dir = Path(__file__).parent / "data"
    ticker_files = list(data_dir.glob("tickers_for_analysis_*.json"))

    if ticker_files:
        # Use most recent file
        latest_file = max(ticker_files, key=lambda p: p.stat().st_mtime)
        print(f"Loading tickers from: {latest_file}")

        with open(latest_file, 'r') as f:
            data = json.load(f)
            tickers = data['tickers']
    else:
        # Fallback to manual list
        print("No screener output found, using sample tickers")
        tickers = ['QLYS', 'DLO', 'DOCN', 'FORM', 'VCYT', 'MGNI', 'GLOB', 'RAMP', 'GDRX', 'RPD', 'YEXT']

    # Run sentiment analysis
    df = analyzer.analyze_batch(tickers, days_back=30)

    # Print summary
    if not df.empty:
        analyzer.print_sentiment_summary(df)


if __name__ == "__main__":
    main()
