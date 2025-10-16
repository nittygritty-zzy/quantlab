"""
Tests for analysis CLI commands

Tests all 2 analyze commands: ticker, portfolio
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from click.testing import CliRunner

from quantlab.cli.analyze import (
    analyze,
    analyze_ticker,
    analyze_portfolio
)


class TestAnalyzeTicker:
    """Tests for 'analyze ticker' command"""

    def test_analyze_ticker_basic(self, cli_runner, sample_analysis_result):
        """Test basic ticker analysis"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {
                "current": 180.50,
                "change_percent": 1.5,
                "volume": 50000000
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '🔍 Analyzing AAPL' in result.output
        assert '$180.50' in result.output
        mock_analyzer.analyze_ticker.assert_called_once_with(
            ticker='AAPL',
            include_options=True,
            include_fundamentals=True,
            include_sentiment=True,
            include_technicals=True
        )

    def test_analyze_ticker_with_no_options(self, cli_runner):
        """Test ticker analysis with options disabled"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "volume": 50000000}
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--no-options'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        call_args = mock_analyzer.analyze_ticker.call_args
        assert call_args[1]['include_options'] is False

    def test_analyze_ticker_with_no_fundamentals(self, cli_runner):
        """Test ticker analysis with fundamentals disabled"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--no-fundamentals'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        call_args = mock_analyzer.analyze_ticker.call_args
        assert call_args[1]['include_fundamentals'] is False

    def test_analyze_ticker_with_no_sentiment(self, cli_runner):
        """Test ticker analysis with sentiment disabled"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--no-sentiment'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        call_args = mock_analyzer.analyze_ticker.call_args
        assert call_args[1]['include_sentiment'] is False

    def test_analyze_ticker_with_no_technicals(self, cli_runner):
        """Test ticker analysis with technicals disabled"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--no-technicals'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        call_args = mock_analyzer.analyze_ticker.call_args
        assert call_args[1]['include_technicals'] is False

    def test_analyze_ticker_all_disabled(self, cli_runner):
        """Test ticker analysis with all optional features disabled"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--no-options', '--no-fundamentals', '--no-sentiment', '--no-technicals'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        call_args = mock_analyzer.analyze_ticker.call_args
        assert call_args[1]['include_options'] is False
        assert call_args[1]['include_fundamentals'] is False
        assert call_args[1]['include_sentiment'] is False
        assert call_args[1]['include_technicals'] is False

    def test_analyze_ticker_with_fundamentals(self, cli_runner):
        """Test ticker analysis displays fundamentals correctly"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000},
            "fundamentals": {
                "pe_ratio": 28.5,
                "forward_pe": 25.0,
                "recommendation": "buy",
                "target_price": 200.0
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '📊 Fundamentals:' in result.output
        assert 'P/E Ratio: 28.50' in result.output
        assert 'Forward P/E: 25.00' in result.output
        assert 'Recommendation: BUY' in result.output
        assert 'Target Price: $200.00' in result.output

    def test_analyze_ticker_with_sentiment(self, cli_runner):
        """Test ticker analysis displays sentiment correctly"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000},
            "sentiment": {
                "label": "positive",
                "score": 0.75,
                "articles_analyzed": 10,
                "positive_articles": 7,
                "negative_articles": 3
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '📰 News Sentiment:' in result.output
        assert 'Label: POSITIVE' in result.output
        assert 'Score: 0.750' in result.output
        assert 'Articles: 10' in result.output

    def test_analyze_ticker_with_technicals(self, cli_runner):
        """Test ticker analysis displays technical indicators correctly"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000},
            "technical_indicators": {
                "current_price": 180.50,
                "trend": {
                    "sma_20": 175.0,
                    "sma_50": 170.0
                },
                "momentum": {
                    "rsi_14": 65.5,
                    "macd_line": 2.5,
                    "macd_signal": 2.0
                },
                "volatility": {
                    "bb_upper": 185.0,
                    "bb_lower": 175.0
                },
                "signals": {
                    "rsi": "neutral",
                    "macd": "bullish",
                    "trend_strength": "strong"
                }
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '📉 Technical Indicators:' in result.output
        assert 'SMA(20): $175.00' in result.output
        assert 'RSI(14): 65.50' in result.output
        assert 'MACD:' in result.output
        assert 'Bollinger Bands:' in result.output

    def test_analyze_ticker_with_options(self, cli_runner):
        """Test ticker analysis displays options correctly"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000},
            "options": {
                "top_itm_calls": [
                    {
                        "strike": 175.0,
                        "expiration": "2025-12-31",
                        "itm_pct": 3.1,
                        "open_interest": 5000,
                        "delta": 0.75,
                        "theta": -0.05,
                        "vanna": 0.001,
                        "charm": -0.0001,
                        "analysis": {"liquidity": "high"},
                        "score": 85.5
                    }
                ]
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '📞 Top ITM Call Recommendations:' in result.output
        assert '$175.00 strike' in result.output
        assert 'Score: 85.5/100' in result.output

    def test_analyze_ticker_with_output_file(self, cli_runner, temp_dir):
        """Test ticker analysis saves to output file"""
        mock_analyzer = Mock()
        analysis_result = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
        }
        mock_analyzer.analyze_ticker.return_value = analysis_result

        output_file = temp_dir / "analysis.json"

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--output', str(output_file)],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '💾 Analysis saved to:' in result.output
        assert output_file.exists()

        # Verify file contents
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data['ticker'] == 'AAPL'
        assert saved_data['status'] == 'success'

    def test_analyze_ticker_creates_output_directory(self, cli_runner, temp_dir):
        """Test ticker analysis creates output directory if needed"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "success",
            "ticker": "AAPL",
            "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
        }

        output_file = temp_dir / "subdir" / "analysis.json"

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL', '--output', str(output_file)],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_analyze_ticker_failed_analysis(self, cli_runner):
        """Test ticker analysis handles analysis failure"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.return_value = {
            "status": "error",
            "error": "Ticker not found"
        }

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'INVALID'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '❌ Analysis failed: Ticker not found' in result.output

    def test_analyze_ticker_exception(self, cli_runner):
        """Test ticker analysis handles exceptions"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_ticker.side_effect = Exception("API error")

        result = cli_runner.invoke(
            analyze,
            ['ticker', 'AAPL'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '❌ Analysis failed: API error' in result.output


class TestAnalyzePortfolio:
    """Tests for 'analyze portfolio' command"""

    def test_analyze_portfolio_basic(self, cli_runner):
        """Test basic portfolio analysis"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "status": "success",
            "portfolio_name": "Tech Stocks",
            "num_positions": 3,
            "tickers": ["AAPL", "GOOGL", "MSFT"],
            "ticker_analyses": {
                "AAPL": {
                    "status": "success",
                    "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
                },
                "GOOGL": {
                    "status": "success",
                    "price": {"current": 2850.0}
                },
                "MSFT": {
                    "status": "success",
                    "price": {"current": 380.0}
                }
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '📊 Analyzing portfolio: tech' in result.output
        assert 'Portfolio: Tech Stocks' in result.output
        assert 'Positions: 3' in result.output
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output
        assert 'MSFT' in result.output
        mock_analyzer.analyze_portfolio.assert_called_once_with(
            portfolio_id='tech',
            include_options=False
        )

    def test_analyze_portfolio_with_options(self, cli_runner):
        """Test portfolio analysis with options included"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "status": "success",
            "portfolio_name": "Tech Stocks",
            "num_positions": 1,
            "tickers": ["AAPL"],
            "ticker_analyses": {
                "AAPL": {
                    "status": "success",
                    "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
                }
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech', '--with-options'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        call_args = mock_analyzer.analyze_portfolio.call_args
        assert call_args[1]['include_options'] is True

    def test_analyze_portfolio_with_aggregate_metrics(self, cli_runner):
        """Test portfolio analysis displays aggregate metrics"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "status": "success",
            "portfolio_name": "Tech Stocks",
            "num_positions": 2,
            "tickers": ["AAPL", "GOOGL"],
            "aggregate_metrics": {
                "average_pe": 27.5,
                "tickers_with_pe": 2,
                "analyst_recommendations": {
                    "buy": 15,
                    "hold": 8,
                    "sell": 2
                }
            },
            "ticker_analyses": {
                "AAPL": {"status": "success", "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}},
                "GOOGL": {"status": "success", "price": {"current": 2850.0}}
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '📈 Portfolio Metrics:' in result.output
        assert 'Average P/E: 27.50' in result.output
        assert '💡 Analyst Recommendations:' in result.output
        assert 'Buy: 15' in result.output

    def test_analyze_portfolio_with_recommendations(self, cli_runner):
        """Test portfolio analysis displays ticker recommendations"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "status": "success",
            "portfolio_name": "Tech Stocks",
            "num_positions": 2,
            "tickers": ["AAPL", "GOOGL"],
            "ticker_analyses": {
                "AAPL": {
                    "status": "success",
                    "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000},
                    "fundamentals": {"recommendation": "buy"}
                },
                "GOOGL": {
                    "status": "success",
                    "price": {"current": 2850.0},
                    "fundamentals": {"recommendation": "hold"}
                }
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert 'Recommendation: BUY' in result.output
        assert 'Recommendation: HOLD' in result.output

    def test_analyze_portfolio_with_errors(self, cli_runner):
        """Test portfolio analysis handles ticker errors"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "status": "success",
            "portfolio_name": "Tech Stocks",
            "num_positions": 2,
            "tickers": ["AAPL", "INVALID"],
            "ticker_analyses": {
                "AAPL": {
                    "status": "success",
                    "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}
                },
                "INVALID": {
                    "status": "error",
                    "error": "Ticker not found"
                }
            }
        }

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert 'AAPL: $180.50' in result.output
        assert 'INVALID: Error - Ticker not found' in result.output

    def test_analyze_portfolio_with_output_file(self, cli_runner, temp_dir):
        """Test portfolio analysis saves to output file"""
        mock_analyzer = Mock()
        analysis_result = {
            "status": "success",
            "portfolio_name": "Tech Stocks",
            "num_positions": 1,
            "tickers": ["AAPL"],
            "ticker_analyses": {
                "AAPL": {"status": "success", "price": {"current": 180.50, "change_percent": 1.5, "volume": 50000000}}
            }
        }
        mock_analyzer.analyze_portfolio.return_value = analysis_result

        output_file = temp_dir / "portfolio_analysis.json"

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech', '--output', str(output_file)],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '💾 Analysis saved to:' in result.output
        assert output_file.exists()

        # Verify file contents
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data['portfolio_name'] == 'Tech Stocks'
        assert saved_data['status'] == 'success'

    def test_analyze_portfolio_failed_analysis(self, cli_runner):
        """Test portfolio analysis handles analysis failure"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "status": "error",
            "error": "Portfolio not found"
        }

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'nonexistent'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '❌ Analysis failed: Portfolio not found' in result.output

    def test_analyze_portfolio_exception(self, cli_runner):
        """Test portfolio analysis handles exceptions"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.side_effect = Exception("Database error")

        result = cli_runner.invoke(
            analyze,
            ['portfolio', 'tech'],
            obj={'analyzer': mock_analyzer}
        )

        assert result.exit_code == 0
        assert '❌ Analysis failed: Database error' in result.output


class TestAnalyzeCommandGroup:
    """Tests for the analyze command group"""

    def test_analyze_help(self, cli_runner):
        """Test that analyze --help displays correctly"""
        result = cli_runner.invoke(analyze, ['--help'])
        assert result.exit_code == 0
        assert 'Analyze tickers and portfolios' in result.output
        assert 'ticker' in result.output
        assert 'portfolio' in result.output

    def test_analyze_has_all_subcommands(self, cli_runner):
        """Test that all expected subcommands are registered"""
        result = cli_runner.invoke(analyze, ['--help'])
        commands = ['ticker', 'portfolio']
        for cmd in commands:
            assert cmd in result.output
