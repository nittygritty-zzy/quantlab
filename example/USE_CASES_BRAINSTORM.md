# Use Cases: Technical Indicator Screeners & Trading Opportunities

## 1. Screener Based on Technical Indicators

### A. Momentum Screeners
**Use Case 1.1: RSI Oversold/Overbought Scanner**
- **Purpose**: Find stocks at extreme RSI levels indicating potential reversals
- **Criteria**: RSI < 30 (oversold) or RSI > 70 (overbought)
- **Extensions**:
  - Multi-timeframe RSI (daily, weekly alignment)
  - RSI divergence detection (price makes new low, RSI doesn't)
  - Custom RSI thresholds per sector/volatility

**Use Case 1.2: MACD Crossover Scanner**
- **Purpose**: Identify stocks with recent MACD signal line crossovers
- **Criteria**: MACD line crosses above/below signal line in last N days
- **Extensions**:
  - Histogram momentum (increasing/decreasing)
  - Zero-line crossovers
  - Combined with price position relative to moving averages

**Use Case 1.3: Stochastic Momentum Index (SMI)**
- **Purpose**: Find stocks with extreme momentum readings
- **Criteria**: %K and %D in oversold/overbought zones
- **Extensions**: Look for %K/%D crossovers in extreme zones

### B. Trend Following Screeners
**Use Case 1.4: Moving Average Golden/Death Cross**
- **Purpose**: Capture major trend changes
- **Criteria**:
  - Golden Cross: 50-day MA crosses above 200-day MA
  - Death Cross: 50-day MA crosses below 200-day MA
- **Extensions**:
  - EMA vs SMA comparisons
  - Multiple MA alignment (20/50/100/200 all aligned)
  - Volume confirmation on crossover

**Use Case 1.5: ADX Trend Strength Filter**
- **Purpose**: Find stocks in strong trending conditions
- **Criteria**: ADX > 25 (strong trend), combined with +DI/-DI direction
- **Extensions**:
  - Rising ADX (strengthening trend)
  - ADX + price pattern confirmation
  - Sector-relative ADX strength

**Use Case 1.6: Bollinger Band Breakout**
- **Purpose**: Identify volatility expansion and breakouts
- **Criteria**: Price breaks above upper band or below lower band
- **Extensions**:
  - Bollinger Band squeeze (low volatility before expansion)
  - Band width percentile ranking
  - Volume surge on breakout

### C. Volume & Liquidity Screeners
**Use Case 1.7: Volume Surge Scanner**
- **Purpose**: Find stocks with unusual volume activity
- **Criteria**: Today's volume > 2x average volume (20-day)
- **Extensions**:
  - Relative volume by time of day
  - Volume + price momentum combo
  - Institutional accumulation patterns (OBV)

**Use Case 1.8: Accumulation/Distribution Line**
- **Purpose**: Detect smart money flow
- **Criteria**: A/D line trending up while price consolidates
- **Extensions**:
  - A/D divergence from price
  - Money Flow Index (MFI) confirmation
  - Chaikin Money Flow for short-term pressure

### D. Volatility & Risk Screeners
**Use Case 1.9: ATR Volatility Filter**
- **Purpose**: Find stocks with optimal volatility for trading strategy
- **Criteria**: ATR within specific range or percentile
- **Extensions**:
  - ATR expansion/contraction phases
  - Normalized ATR (ATR/price) for comparisons
  - Volatility breakout from low ATR

**Use Case 1.10: Beta-Adjusted Stock Scanner**
- **Purpose**: Find stocks with specific market correlation
- **Criteria**: Beta > 1.5 (high volatility) or Beta < 0.5 (defensive)
- **Extensions**:
  - Rolling beta calculations
  - Sector-relative beta
  - Beta + volatility combo filters

### E. Pattern Recognition Screeners
**Use Case 1.11: Support/Resistance Breakout**
- **Purpose**: Identify price breaking key levels
- **Criteria**: Price crosses significant historical S/R level
- **Extensions**:
  - Volume confirmation
  - Retest opportunities after breakout
  - Multiple timeframe S/R alignment

**Use Case 1.12: Fibonacci Retracement Levels**
- **Purpose**: Find stocks at key retracement levels
- **Criteria**: Price at 38.2%, 50%, or 61.8% retracement
- **Extensions**:
  - Confluence with other indicators
  - Extension levels for targets
  - Multiple swing analysis

### F. Multi-Factor Composite Screeners
**Use Case 1.13: Bull/Bear Signal Composite**
- **Purpose**: Score stocks based on multiple aligned indicators
- **Criteria**: Weighted scoring system (e.g., RSI + MACD + Volume + Trend)
- **Example Scoring**:
  - RSI < 30: +2 points (bullish)
  - MACD crossover up: +2 points
  - Volume > 2x avg: +1 point
  - Price > 50MA: +1 point
  - Total score 5-6: Strong buy signal

**Use Case 1.14: Sector Rotation Scanner**
- **Purpose**: Identify strongest sectors and stocks within them
- **Criteria**: Relative strength vs sector + absolute indicators
- **Extensions**:
  - Sector momentum rankings
  - Leadership changes
  - Inter-market analysis

**Use Case 1.15: Mean Reversion Setup**
- **Purpose**: Find extreme deviations for reversion trades
- **Criteria**: Price > 2 std devs from mean + other oversold signals
- **Extensions**:
  - Z-score calculations
  - Historical reversion success rate
  - Catalyst checks (earnings, news)

---

## 2. Finding Buying/Selling Opportunities for a Stock

### A. Entry Signals (Buying Opportunities)

**Use Case 2.1: Pullback to Support in Uptrend**
- **Signal**: Price pulls back to key MA (20/50 EMA) in confirmed uptrend
- **Confirmation**:
  - Price bounces off MA with bullish candle
  - RSI > 40 (not oversold)
  - Volume decreases on pullback, increases on bounce
- **Risk Management**: Stop below recent swing low

**Use Case 2.2: Bullish Divergence Setup**
- **Signal**: Price makes lower low, RSI/MACD makes higher low
- **Confirmation**:
  - Price breaks above recent swing high
  - Volume expansion on breakout
  - Other oscillators confirm (Stochastic, CCI)
- **Target**: Previous resistance or measured move

**Use Case 2.3: Consolidation Breakout**
- **Signal**: Price breaks above consolidation range on volume
- **Confirmation**:
  - Volume > 1.5x average
  - Multiple attempts at resistance level
  - Tight consolidation (low ATR)
- **Entry**: Break of range high + 0.5 ATR
- **Stop**: Below consolidation low

**Use Case 2.4: Moving Average Convergence Buy**
- **Signal**: Price near multiple MAs converging (20/50/200)
- **Confirmation**:
  - All MAs starting to slope upward
  - Price closes above all MAs
  - Volume pickup
- **Psychology**: High probability trend initiation point

**Use Case 2.5: Oversold Bounce in Strong Stock**
- **Signal**: Quality stock (strong fundamentals) becomes oversold
- **Criteria**:
  - RSI < 30 on daily chart
  - Price at or near 200-day MA (first touch in uptrend)
  - Weekly chart still bullish
- **Confirmation**: Bullish reversal candle pattern
- **Stop**: Below 200-day MA

**Use Case 2.6: Gap Fill Opportunity**
- **Signal**: Stock gaps down on no major news in uptrend
- **Entry**: After initial panic selling stabilizes
- **Target**: Gap fill level
- **Confirmation**: Volume dries up, accumulation begins

### B. Exit Signals (Selling Opportunities)

**Use Case 2.7: Resistance Rejection Exit**
- **Signal**: Price approaches major resistance with weakening momentum
- **Indicators**:
  - RSI overbought (> 70) + bearish divergence
  - Multiple touches of resistance
  - Volume decreasing on rallies
- **Action**: Take partial/full profits

**Use Case 2.8: Moving Average Break Exit**
- **Signal**: Price closes below key MA that held during uptrend
- **Triggers**:
  - Break of 20 EMA on increasing volume
  - 50-day MA violation in strong uptrend
  - 200-day MA break = major trend change
- **Action**: Exit or tighten stops significantly

**Use Case 2.9: Parabolic Move Exhaustion**
- **Signal**: Vertical price rise with extreme volume/volatility
- **Indicators**:
  - RSI > 80 for multiple days
  - Bollinger Bands extremely wide
  - Gap ups on opening
  - News/social media frenzy
- **Action**: Scale out, use trailing stops

**Use Case 2.10: Bearish Divergence Exit**
- **Signal**: Price makes new high, indicators don't confirm
- **Divergence Types**:
  - RSI lower high while price higher high
  - MACD histogram declining
  - Volume declining on rallies
- **Action**: Exit longs, consider shorts

**Use Case 2.11: Failed Breakout Exit**
- **Signal**: Breakout reverses quickly (bull trap)
- **Recognition**:
  - Price breaks resistance but closes back below
  - Low volume on breakout
  - Quick reversal within 1-3 days
- **Action**: Immediate exit to minimize loss

**Use Case 2.12: Time-Based Exit**
- **Signal**: Position held for target timeframe without progress
- **Triggers**:
  - Swing trade: 5-10 days with no meaningful move
  - Dead money opportunity cost
  - Market environment changed
- **Action**: Exit and redeploy capital

### C. Advanced Opportunity Detection

**Use Case 2.13: Multi-Timeframe Alignment**
- **Purpose**: Find highest probability setups
- **Method**:
  - Weekly: Identify trend direction
  - Daily: Find pullback/setup
  - 4H/1H: Fine-tune entry timing
- **Example**: Weekly uptrend + daily pullback to 50MA + hourly bullish engulfing

**Use Case 2.14: Options Market Signal Integration**
- **Purpose**: Use options data for directional bias
- **Signals**:
  - Put/Call ratio extremes
  - Unusual options activity (large sweeps)
  - Implied volatility changes
  - Max pain levels near expiration
- **Action**: Confirm stock trade direction with options flow

**Use Case 2.15: News/Catalyst-Driven Opportunities**
- **Purpose**: Trade around scheduled events
- **Events**:
  - Earnings announcements (pre/post move)
  - FDA approvals (biotech)
  - Economic data releases
  - Product launches
- **Strategy**:
  - Pre-event positioning (IV crush awareness)
  - Post-event continuation/reversal
  - News sentiment analysis

**Use Case 2.16: Relative Strength Opportunities**
- **Purpose**: Trade stocks outperforming sector/market
- **Method**:
  - Compare stock to SPY/sector ETF
  - Find stocks making new highs while market flat
  - Rank stocks by RS over multiple timeframes
- **Edge**: Strong stocks stay strong (momentum persistence)

**Use Case 2.17: Volatility Contraction Setup**
- **Purpose**: Trade the expansion after contraction
- **Signals**:
  - Bollinger Band squeeze (narrow bands)
  - Low ATR reading (historically low)
  - Tight consolidation pattern
- **Entry**: Breakout of consolidation in direction of trend
- **Edge**: Volatility tends to cluster (low vol → high vol)

**Use Case 2.18: Smart Money Divergence**
- **Purpose**: Follow institutional accumulation/distribution
- **Indicators**:
  - OBV rising while price flat (accumulation)
  - Dark pool activity increase
  - Large block trades
  - Decreasing float availability
- **Action**: Position before retail notices

### D. Risk Management Opportunities

**Use Case 2.19: Trailing Stop Adjustments**
- **Purpose**: Lock in profits while allowing trend to run
- **Methods**:
  - ATR-based trailing stop (2-3x ATR)
  - Moving average trailing stop (20/50 EMA)
  - Chandelier exit
  - Percentage-based (5-10%)
- **Trigger**: Move stop to breakeven after 1R profit

**Use Case 2.20: Position Sizing Based on Volatility**
- **Purpose**: Adjust size based on stock's risk profile
- **Method**:
  - Calculate shares: (Risk $ per trade) / (ATR × Multiplier)
  - Lower size for high volatility stocks
  - Higher size for low volatility stocks
- **Goal**: Normalize risk across all positions

---

## Implementation Priority Suggestions

### Phase 1: Core Screeners (Week 1-2)
1. RSI Oversold/Overbought Scanner
2. MACD Crossover Scanner
3. Volume Surge Scanner
4. Moving Average Golden Cross
5. Support/Resistance Breakout

### Phase 2: Opportunity Detection (Week 3-4)
1. Pullback to Support in Uptrend
2. Consolidation Breakout
3. Resistance Rejection Exit
4. Moving Average Break Exit
5. Multi-Timeframe Alignment

### Phase 3: Advanced Features (Week 5-6)
1. Composite Scoring System
2. Divergence Detection (bull/bear)
3. Volatility-based Position Sizing
4. Relative Strength Analysis
5. Backtesting framework for each signal

### Phase 4: Integration & Optimization (Week 7-8)
1. Real-time alert system
2. Dashboard for monitoring multiple stocks
3. Performance tracking for each signal type
4. Machine learning signal optimization
5. Portfolio-level risk management

---

## Technical Architecture Considerations

### Data Requirements
- OHLCV data (minute/daily/weekly)
- Technical indicators (pre-calculated or on-the-fly)
- Fundamental data (optional, for filtering)
- News/sentiment data (optional, for catalyst identification)
- Options data (optional, for advanced strategies)

### Performance Optimization
- Vectorized calculations (pandas/numpy)
- Incremental updates (only new data)
- Caching commonly used indicators
- Parallel processing for multi-stock scans
- Database indexing for fast queries

### User Interface Ideas
- Web dashboard with real-time updates
- Configurable alert thresholds
- Backtesting interface for strategy validation
- Chart visualization with indicator overlays
- Watchlist management with custom filters

### Integration with QuantLab
- Use qlib for data handling
- MLflow for tracking screener performance
- Configuration files for different strategies
- Results saved to `results/screeners/`
- Scripts in `scripts/analysis/screeners/`
