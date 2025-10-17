"""
Technical Analysis and Trading Strategies for Profitable Small-Cap AI Stocks

Provides:
1. Technical indicator calculations
2. Trading strategy recommendations
3. Entry/exit signals
4. Risk management suggestions
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import json


class TechnicalAnalyzer:
    """Technical analysis and strategy generator"""

    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.analysis_dir = Path(__file__).parent / "analysis"
        self.strategies_dir = Path(__file__).parent / "strategies"

        for dir in [self.data_dir, self.analysis_dir, self.strategies_dir]:
            dir.mkdir(exist_ok=True)

    def get_price_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Get historical price data"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            return df
        except Exception as e:
            print(f"Error fetching price data for {ticker}: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        if df.empty:
            return df

        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

        # ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()

        # Volume indicators
        df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']

        # Price momentum
        df['ROC'] = df['Close'].pct_change(periods=10) * 100  # 10-day rate of change
        df['Momentum'] = df['Close'] - df['Close'].shift(10)

        # Support and Resistance (recent highs/lows)
        df['Resistance'] = df['High'].rolling(window=20).max()
        df['Support'] = df['Low'].rolling(window=20).min()

        return df

    def analyze_stock(self, ticker: str, period: str = "1y") -> Dict:
        """
        Perform complete technical analysis on a stock

        Returns:
            Dictionary with analysis results and strategy recommendations
        """
        print(f"Analyzing {ticker}...", end=" ")

        df = self.get_price_data(ticker, period)

        if df.empty:
            print("❌ No data")
            return {}

        df = self.calculate_indicators(df)

        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # Current price position
        current_price = latest['Close']
        sma_20 = latest['SMA_20']
        sma_50 = latest['SMA_50']
        sma_200 = latest['SMA_200'] if not pd.isna(latest['SMA_200']) else None

        # Trend analysis
        trend = self._determine_trend(latest, sma_20, sma_50, sma_200)

        # Momentum analysis
        rsi = latest['RSI']
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']

        # Volatility
        atr = latest['ATR']
        bb_width = latest['BB_Width']

        # Volume analysis
        volume_ratio = latest['Volume_Ratio']

        # Generate signals and strategies
        signals = self._generate_signals(latest, prev, df)
        strategies = self._recommend_strategies(ticker, latest, df, trend, signals)

        analysis = {
            'ticker': ticker,
            'analysis_date': datetime.now().isoformat(),
            'current_price': current_price,

            'trend': trend,

            'indicators': {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'sma_200': sma_200,
                'rsi': rsi,
                'macd': macd,
                'macd_signal': macd_signal,
                'atr': atr,
                'atr_percent': (atr / current_price) * 100,
                'bb_width': bb_width,
                'volume_ratio': volume_ratio,
            },

            'price_levels': {
                'support': latest['Support'],
                'resistance': latest['Resistance'],
                'bb_upper': latest['BB_Upper'],
                'bb_lower': latest['BB_Lower'],
            },

            'signals': signals,
            'strategies': strategies,

            'timestamp': datetime.now().isoformat()
        }

        print("✅")
        return analysis

    def _determine_trend(self, latest, sma_20, sma_50, sma_200) -> str:
        """Determine overall trend"""
        price = latest['Close']

        # Check MA alignment
        if sma_200 and price > sma_20 > sma_50 > sma_200:
            return 'Strong Uptrend'
        elif sma_200 and price > sma_200:
            return 'Uptrend'
        elif sma_200 and price < sma_20 < sma_50 < sma_200:
            return 'Strong Downtrend'
        elif sma_200 and price < sma_200:
            return 'Downtrend'
        else:
            return 'Sideways/Consolidation'

    def _generate_signals(self, latest, prev, df: pd.DataFrame) -> Dict:
        """Generate trading signals"""
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }

        price = latest['Close']
        rsi = latest['RSI']
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']
        bb_upper = latest['BB_Upper']
        bb_lower = latest['BB_Lower']

        # RSI signals
        if rsi < 30:
            signals['buy_signals'].append('RSI Oversold (<30)')
        elif rsi > 70:
            signals['sell_signals'].append('RSI Overbought (>70)')
        elif 30 <= rsi <= 50:
            signals['buy_signals'].append('RSI in buy zone (30-50)')

        # MACD signals
        if macd > macd_signal and prev['MACD'] <= prev['MACD_Signal']:
            signals['buy_signals'].append('MACD Bullish Crossover')
        elif macd < macd_signal and prev['MACD'] >= prev['MACD_Signal']:
            signals['sell_signals'].append('MACD Bearish Crossover')

        # Moving Average signals
        if price > latest['SMA_50'] and prev['Close'] <= prev['SMA_50']:
            signals['buy_signals'].append('Price crossed above 50-day SMA')
        elif price < latest['SMA_50'] and prev['Close'] >= prev['SMA_50']:
            signals['sell_signals'].append('Price crossed below 50-day SMA')

        # Bollinger Band signals
        if price < bb_lower:
            signals['buy_signals'].append('Price below lower Bollinger Band')
        elif price > bb_upper:
            signals['sell_signals'].append('Price above upper Bollinger Band')

        # Golden/Death Cross
        if latest['SMA_50'] > latest['SMA_200'] and prev['SMA_50'] <= prev['SMA_200']:
            signals['buy_signals'].append('🌟 Golden Cross (50 MA > 200 MA)')
        elif latest['SMA_50'] < latest['SMA_200'] and prev['SMA_50'] >= prev['SMA_200']:
            signals['sell_signals'].append('💀 Death Cross (50 MA < 200 MA)')

        # Volume confirmation
        if latest['Volume_Ratio'] > 1.5:
            signals['neutral_signals'].append(f"High volume ({latest['Volume_Ratio']:.1f}x average)")

        return signals

    def _recommend_strategies(self, ticker: str, latest, df: pd.DataFrame,
                             trend: str, signals: Dict) -> List[Dict]:
        """Recommend trading strategies based on analysis"""
        strategies = []

        price = latest['Close']
        atr = latest['ATR']
        rsi = latest['RSI']
        bb_width = latest['BB_Width']

        # Strategy 1: Trend Following
        if 'Uptrend' in trend:
            strategies.append({
                'strategy': 'Trend Following - Long',
                'entry': 'On pullback to 20-day SMA',
                'stop_loss': price - (2 * atr),
                'take_profit_1': price + (2 * atr),
                'take_profit_2': price + (3 * atr),
                'position_size': 'Based on ATR risk',
                'rationale': f'{trend} with bullish momentum',
                'risk_reward': '1:2 to 1:3'
            })

        # Strategy 2: Mean Reversion
        if rsi < 30 or price < latest['BB_Lower']:
            strategies.append({
                'strategy': 'Mean Reversion - Long',
                'entry': f'Current price (${price:.2f}) is oversold',
                'stop_loss': latest['Support'],
                'take_profit_1': latest['BB_Middle'],
                'take_profit_2': latest['SMA_20'],
                'position_size': 'Half position initially, scale in if lower',
                'rationale': 'Oversold conditions, likely bounce',
                'risk_reward': '1:2'
            })

        # Strategy 3: Breakout
        resistance_near = abs(price - latest['Resistance']) / price < 0.02  # Within 2%
        if resistance_near and latest['Volume_Ratio'] > 1.2:
            strategies.append({
                'strategy': 'Breakout Trading',
                'entry': f'Above ${latest["Resistance"]:.2f} (resistance)',
                'stop_loss': latest['SMA_20'],
                'take_profit_1': latest['Resistance'] + (latest['Resistance'] - latest['Support']),
                'take_profit_2': latest['Resistance'] + 2 * (latest['Resistance'] - latest['Support']),
                'position_size': 'Normal position on confirmed breakout',
                'rationale': 'Near resistance with volume pickup',
                'risk_reward': '1:2 to 1:3'
            })

        # Strategy 4: Volatility Contraction
        if bb_width < 0.1:  # Bollinger Bands are tight
            strategies.append({
                'strategy': 'Volatility Expansion Play',
                'entry': 'Breakout from consolidation (either direction)',
                'stop_loss': 'Opposite side of consolidation range',
                'take_profit_1': 'ATR-based target',
                'position_size': 'Smaller due to directional uncertainty',
                'rationale': 'Bollinger Band squeeze - volatility likely to expand',
                'risk_reward': '1:2'
            })

        # Strategy 5: Pullback in Uptrend
        if trend == 'Strong Uptrend' and 40 <= rsi <= 50:
            strategies.append({
                'strategy': 'Pullback Buy in Uptrend',
                'entry': f'At 20-day SMA (${latest["SMA_20"]:.2f})',
                'stop_loss': latest['SMA_50'],
                'take_profit_1': latest['Resistance'],
                'take_profit_2': latest['Resistance'] * 1.05,
                'position_size': 'Standard position',
                'rationale': 'Healthy pullback in strong uptrend',
                'risk_reward': '1:2+'
            })

        return strategies

    def analyze_batch(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        """Analyze multiple tickers"""
        print("\n" + "="*80)
        print("TECHNICAL ANALYSIS")
        print("="*80)
        print(f"Analyzing {len(tickers)} stocks")
        print("="*80 + "\n")

        results = []

        for ticker in tickers:
            analysis = self.analyze_stock(ticker, period)
            if analysis:
                results.append(analysis)

        # Save results
        output_file = self.analysis_dir / f"technical_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Technical analysis saved to: {output_file}")

        return results

    def generate_strategy_report(self, analyses: List[Dict]):
        """Generate a comprehensive strategy report"""
        print("\n" + "="*80)
        print("TRADING STRATEGY RECOMMENDATIONS")
        print("="*80)

        for analysis in analyses:
            ticker = analysis['ticker']
            price = analysis['current_price']
            trend = analysis['trend']
            signals = analysis['signals']
            strategies = analysis['strategies']

            print(f"\n{'='*80}")
            print(f"📊 {ticker} - ${price:.2f} | Trend: {trend}")
            print(f"{'='*80}")

            # Signals
            if signals['buy_signals']:
                print(f"\n🟢 BUY SIGNALS:")
                for signal in signals['buy_signals']:
                    print(f"   • {signal}")

            if signals['sell_signals']:
                print(f"\n🔴 SELL SIGNALS:")
                for signal in signals['sell_signals']:
                    print(f"   • {signal}")

            if signals['neutral_signals']:
                print(f"\n⚪ NEUTRAL SIGNALS:")
                for signal in signals['neutral_signals']:
                    print(f"   • {signal}")

            # Recommended Strategies
            if strategies:
                print(f"\n💡 RECOMMENDED STRATEGIES:")
                for i, strat in enumerate(strategies, 1):
                    print(f"\n   Strategy {i}: {strat['strategy']}")
                    print(f"   ├─ Entry: {strat['entry']}")
                    print(f"   ├─ Stop Loss: ${strat['stop_loss']:.2f}" if isinstance(strat['stop_loss'], (int, float)) else f"   ├─ Stop Loss: {strat['stop_loss']}")
                    print(f"   ├─ Take Profit 1: ${strat['take_profit_1']:.2f}" if isinstance(strat['take_profit_1'], (int, float)) else f"   ├─ Take Profit 1: {strat['take_profit_1']}")
                    print(f"   ├─ Position Size: {strat['position_size']}")
                    print(f"   ├─ Rationale: {strat['rationale']}")
                    print(f"   └─ Risk/Reward: {strat['risk_reward']}")
            else:
                print(f"\n⚠️  No clear strategy signals at this time - wait for better setup")

        print("\n" + "="*80)

        # Save strategy report
        report_file = self.strategies_dir / f"strategy_report_{datetime.now().strftime('%Y%m%d')}.txt"
        # Would save report here


def main():
    """Run technical analysis"""
    analyzer = TechnicalAnalyzer()

    # Load tickers
    data_dir = Path(__file__).parent / "data"
    ticker_files = list(data_dir.glob("tickers_for_analysis_*.json"))

    if ticker_files:
        latest_file = max(ticker_files, key=lambda p: p.stat().st_mtime)
        print(f"Loading tickers from: {latest_file}")

        with open(latest_file, 'r') as f:
            data = json.load(f)
            tickers = data['tickers']
    else:
        print("No screener output found, using sample tickers")
        tickers = ['QLYS', 'DLO', 'DOCN', 'FORM', 'VCYT', 'MGNI', 'GLOB', 'RAMP', 'GDRX', 'RPD', 'YEXT']

    # Analyze stocks
    analyses = analyzer.analyze_batch(tickers, period="1y")

    # Generate strategy report
    if analyses:
        analyzer.generate_strategy_report(analyses)


if __name__ == "__main__":
    main()
