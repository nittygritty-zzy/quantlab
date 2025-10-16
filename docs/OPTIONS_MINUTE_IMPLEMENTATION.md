# Adding Options Minute Support to QuantLab

## Current Status

Options minute data **exists** in the dataset but is **not queryable** yet through the CLI.

- ✅ Data available: 2024-01 through 2025-10
- ✅ Code structure ready
- ❌ Query function not implemented
- ❌ CLI command not exposed

## Why Not Implemented Yet

### 1. Data Volume Challenge
```
Daily options: ~50 MB per ticker per day
Minute options: ~2-5 GB per ticker per day (100+ contracts × 390 minutes)
```

### 2. Query Performance
Options minute queries need:
- Efficient strike price filtering
- Expiration date indexing
- Time-series joins with underlying
- Greeks calculation at each minute

### 3. Use Case Specificity
Most trading strategies use:
- **Daily options** ← Primary use case ✅
- **Minute stocks** ← Supported ✅
- **Minute options** ← Specialized HFT/market making

## Implementation Plan

### Step 1: Add Query Function

Add to `quantlab/data/parquet_reader.py`:

```python
def get_options_minute(
    self,
    underlying_tickers: List[str],
    start_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
    option_type: Optional[str] = None,
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
    expiration_start: Optional[date] = None,
    expiration_end: Optional[date] = None,
    limit: Optional[int] = None
):
    """
    Query minute-level options data from Parquet files

    WARNING: This query can return MASSIVE datasets. Use filters carefully.

    Args:
        underlying_tickers: List of underlying ticker symbols
        start_datetime: Start datetime (default: last trading day)
        end_datetime: End datetime
        option_type: 'call' or 'put'
        min_strike: Minimum strike price
        max_strike: Maximum strike price
        expiration_start: Minimum expiration date
        expiration_end: Maximum expiration date
        limit: Row limit (HIGHLY RECOMMENDED)

    Returns:
        Pandas DataFrame with minute-level options data

    Example:
        # Get AAPL calls near-the-money for last trading day
        df = reader.get_options_minute(
            underlying_tickers=['AAPL'],
            start_datetime=datetime(2025, 10, 15, 9, 30),
            end_datetime=datetime(2025, 10, 15, 16, 0),
            option_type='call',
            min_strike=175,
            max_strike=185,
            limit=10000
        )
    """
    if not self.options_minute_path.exists():
        logger.warning(f"Options minute path does not exist: {self.options_minute_path}")
        return None

    try:
        # Build query with strong filters to prevent OOM
        query_parts = [
            """SELECT
                timestamp,
                underlying_ticker,
                contract_ticker,
                strike_price,
                expiration_date,
                option_type,
                bid,
                ask,
                last,
                volume,
                open_interest,
                implied_volatility,
                delta,
                gamma,
                theta,
                vega
            """
        ]

        parquet_pattern = str(self.options_minute_path / "**/*.parquet")
        query_parts.append(f"FROM '{parquet_pattern}'")

        # Add filters - CRITICAL for performance
        where_clauses = []

        if underlying_tickers:
            ticker_list = ", ".join(f"'{t}'" for t in underlying_tickers)
            where_clauses.append(f"underlying_ticker IN ({ticker_list})")

        if start_datetime:
            where_clauses.append(f"timestamp >= '{start_datetime}'")

        if end_datetime:
            where_clauses.append(f"timestamp <= '{end_datetime}'")

        if option_type:
            where_clauses.append(f"option_type = '{option_type}'")

        if min_strike:
            where_clauses.append(f"strike_price >= {min_strike}")

        if max_strike:
            where_clauses.append(f"strike_price <= {max_strike}")

        if expiration_start:
            where_clauses.append(f"expiration_date >= '{expiration_start}'")

        if expiration_end:
            where_clauses.append(f"expiration_date <= '{expiration_end}'")

        if not where_clauses:
            logger.error("At least one filter is required for options_minute queries!")
            raise ValueError("Must specify filters to prevent reading entire dataset")

        query_parts.append("WHERE " + " AND ".join(where_clauses))

        # Order and limit
        query_parts.append("ORDER BY timestamp DESC, underlying_ticker, strike_price")

        if limit:
            query_parts.append(f"LIMIT {limit}")
        else:
            logger.warning("No limit specified - query may be very slow!")
            query_parts.append("LIMIT 100000")  # Safety limit

        query = "\n".join(query_parts)

        logger.info(f"Querying options minute data for {len(underlying_tickers)} tickers")
        logger.warning(f"Options minute queries can be large - consider using smaller time ranges")

        # Execute query
        result = duckdb.sql(query).df()

        logger.info(f"✓ Retrieved {len(result)} rows of minute options data")
        return result

    except Exception as e:
        logger.error(f"Failed to query options minute data: {e}")
        raise
```

### Step 2: Add CLI Command

Add to `quantlab/cli/data.py`:

```python
@data.command()
@click.argument("tickers", nargs=-1, required=True)
@click.option("--start", help="Start datetime (YYYY-MM-DD HH:MM)")
@click.option("--end", help="End datetime (YYYY-MM-DD HH:MM)")
@click.option("--type", "option_type", type=click.Choice(["call", "put"]))
@click.option("--min-strike", type=float, help="Minimum strike price")
@click.option("--max-strike", type=float, help="Maximum strike price")
@click.option("--limit", type=int, default=10000, help="Row limit (default: 10000)")
@click.pass_obj
def minute_options(cli_ctx, tickers, start, end, option_type, min_strike, max_strike, limit):
    """
    Query minute-level options data

    WARNING: Options minute data is VERY large. Always use filters!

    Examples:

        # Get AAPL calls from 9:30-10:00 AM today
        quantlab data minute-options AAPL \\
            --start "2025-10-15 09:30" \\
            --end "2025-10-15 10:00" \\
            --type call \\
            --min-strike 175 \\
            --max-strike 185 \\
            --limit 1000
    """
    parquet = cli_ctx["parquet"]

    # Parse datetimes
    from datetime import datetime
    start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M") if start else None
    end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M") if end else None

    # Query
    df = parquet.get_options_minute(
        underlying_tickers=list(tickers),
        start_datetime=start_dt,
        end_datetime=end_dt,
        option_type=option_type,
        min_strike=min_strike,
        max_strike=max_strike,
        limit=limit
    )

    if df is None or df.empty:
        click.echo("❌ No data found")
        return

    # Display summary
    click.echo(f"📊 Options Minute Data: {len(df)} rows")
    click.echo(f"\nTime Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    click.echo(f"Tickers: {', '.join(df['underlying_ticker'].unique())}")
    click.echo(f"Contracts: {df['contract_ticker'].nunique()}")

    # Show sample
    click.echo("\n📋 Sample (first 10 rows):")
    click.echo(df.head(10).to_string(index=False))
```

### Step 3: Performance Optimization

**Recommended Usage Pattern**:

```python
# GOOD: Focused query
df = reader.get_options_minute(
    underlying_tickers=['AAPL'],
    start_datetime=datetime(2025, 10, 15, 9, 30),
    end_datetime=datetime(2025, 10, 15, 10, 0),  # 30 minutes
    option_type='call',
    min_strike=175,
    max_strike=185,
    limit=1000
)

# BAD: Too broad
df = reader.get_options_minute(
    underlying_tickers=['AAPL'],  # No time filter!
    limit=1000000  # Way too many rows
)
```

**Tips**:
1. Always specify `start_datetime` and `end_datetime`
2. Use strike price filters to reduce data
3. Query one ticker at a time for large date ranges
4. Use `limit` parameter generously
5. Consider aggregating to 5-minute bars if you don't need every minute

### Step 4: Add Tests

Add to `tests/cli/test_data.py`:

```python
class TestDataMinuteOptions:
    """Test minute-level options queries"""

    def test_query_minute_options_basic(self, cli_runner, mock_cli_dependencies):
        """Test basic minute options query"""
        # Mock return data
        mock_df = pd.DataFrame({
            'timestamp': ['2025-10-15 09:30:00'],
            'underlying_ticker': ['AAPL'],
            'strike_price': [180.0],
            'bid': [2.50],
            'ask': [2.55]
        })

        mock_cli_dependencies['parquet'].get_options_minute.return_value = mock_df

        result = cli_runner.invoke(
            data,
            ['minute-options', 'AAPL',
             '--start', '2025-10-15 09:30',
             '--end', '2025-10-15 10:00',
             '--type', 'call'],
            obj=mock_cli_dependencies
        )

        assert result.exit_code == 0
        assert '📊 Options Minute Data' in result.output

    def test_query_minute_options_requires_filters(self, cli_runner, mock_cli_dependencies):
        """Test that minute options requires filters"""
        # Should fail without time range
        result = cli_runner.invoke(
            data,
            ['minute-options', 'AAPL'],
            obj=mock_cli_dependencies
        )

        assert result.exit_code != 0
```

## Data Volume Considerations

### Typical Sizes

| Query Scope | Estimated Rows | Estimated Size |
|-------------|---------------|----------------|
| 1 ticker, 1 minute, ATM options | ~10 rows | <1 KB |
| 1 ticker, 30 minutes, ATM ±5 strikes | ~500 rows | ~50 KB |
| 1 ticker, 1 hour, all strikes | ~5,000 rows | ~500 KB |
| 1 ticker, 1 day, all strikes | ~40,000 rows | ~4 MB |
| 10 tickers, 1 day, all strikes | ~400,000 rows | ~40 MB |
| 1 ticker, 1 month, all strikes | ~800,000 rows | ~80 MB |

### Memory Requirements

For safe querying:
- **< 100K rows**: Safe for all systems
- **100K - 1M rows**: Needs 4GB+ RAM
- **1M+ rows**: Needs 16GB+ RAM, careful query planning

## Use Cases for Options Minute

### 1. Intraday Volatility Analysis
```bash
# Track IV changes during earnings announcement
quantlab data minute-options NVDA \
    --start "2025-10-15 15:30" \
    --end "2025-10-15 16:00" \
    --type call \
    --min-strike 480 \
    --max-strike 520
```

### 2. Options Flow Detection
```bash
# Detect large volume spikes
quantlab data minute-options SPY \
    --start "2025-10-15 09:30" \
    --end "2025-10-15 09:45" \
    --type put \
    --limit 5000
```

### 3. Market Making Research
```bash
# Analyze bid-ask spreads intraday
quantlab data minute-options AAPL \
    --start "2025-10-15 10:00" \
    --end "2025-10-15 11:00" \
    --min-strike 175 \
    --max-strike 185
```

### 4. Greeks Dynamics
```bash
# Track gamma exposure through the day
quantlab data minute-options QQQ \
    --start "2025-10-15 09:30" \
    --end "2025-10-15 16:00" \
    --type call
```

## Future Enhancements

### 1. Aggregation Functions
```python
# Aggregate to 5-minute bars
df_5min = reader.get_options_minute_aggregated(
    tickers=['AAPL'],
    start_datetime=...,
    interval='5min'
)
```

### 2. Streaming API
```python
# Stream live options minute data
for minute_data in reader.stream_options_minute(['AAPL']):
    analyze_options_flow(minute_data)
```

### 3. Greeks Calculation
```python
# Calculate Greeks on-the-fly
df = reader.get_options_minute(
    ...,
    calculate_greeks=True,
    underlying_price_source='live'
)
```

## Conclusion

**Why not implemented yet**:
1. 📊 Daily options covers 90% of use cases
2. 💾 Minute data requires careful memory management
3. 🎯 Most users don't need sub-daily granularity
4. 🚀 Other features were higher priority

**How to add it**:
1. Implement `get_options_minute()` in `parquet_reader.py`
2. Add CLI command with strict filters
3. Add comprehensive tests
4. Document performance considerations

The data exists and is ready - this is just a matter of implementation priority!
