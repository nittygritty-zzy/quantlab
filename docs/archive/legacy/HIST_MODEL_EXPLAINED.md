# HIST Model Explained

## What is HIST?

**HIST** = **H**idden-concept **I**nformation for **S**tock **T**rend forecasting

**Paper**: "HIST: A Graph-based Framework for Stock Trend Forecasting via Mining Concept-Oriented Shared Information" (2021)
**Link**: https://arxiv.org/abs/2110.13716

---

## The Core Idea

### The Problem HIST Solves

Traditional ML models (XGBoost, LightGBM, Linear Regression) treat each stock **independently**:

```
XGBoost approach:
Stock A features → Predict return for A (independent)
Stock B features → Predict return for B (independent)
Stock C features → Predict return for C (independent)

Problem: Ignores cross-sectional relationships!
- Apple and Microsoft are both tech → Should move together
- Tesla and Ford are both auto → Should have similar patterns
- Banks often move as a group → Shared sector dynamics
```

HIST explicitly models **relationships between stocks** through **shared concepts**.

---

## HIST Architecture

### Three Types of Information

HIST decomposes each stock's representation into 3 components:

```
Stock representation = Explicit Shared + Implicit Shared + Individual

1. Explicit Shared Info: Predefined concepts (sector, industry, market cap)
2. Implicit Shared Info: Hidden concepts learned from data
3. Individual Info: Stock-specific idiosyncratic patterns
```

### Visual Architecture

```
Input: Stock features (Alpha360/Alpha158)
              ↓
         GRU/LSTM (temporal patterns)
              ↓
         Stock Hidden State
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
Predefined Concepts   Hidden Concepts
(Sector, Industry)   (Learned from data)
    ↓                   ↓
Stock-to-Concept    Stock-to-Stock
  Attention           Similarity
    ↓                   ↓
Explicit Shared      Implicit Shared
  Information          Information
    ↓                   ↓
    └─────────┬─────────┘
              ↓
       Individual Info
   (Residual after removing shared)
              ↓
    Final Prediction (weighted sum)
```

### Key Components

#### 1. Predefined Concept Module (Explicit)

Uses **stock-to-concept matrix** (e.g., which sector each stock belongs to):

```python
# Example stock2concept matrix
         Tech   Finance   Energy   Auto
AAPL     1.0     0.0      0.0     0.0
MSFT     1.0     0.0      0.0     0.0
JPM      0.0     1.0      0.0     0.0
TSLA     0.0     0.0      0.0     1.0
XOM      0.0     0.0      1.0     0.0

# HIST learns:
"AAPL and MSFT share Tech concept → Similar behavior"
"When Tech sector is strong, AAPL/MSFT both benefit"
```

**Process**:
1. Aggregate stock features into concept representations
2. Use attention mechanism to learn concept-to-stock influence
3. Extract explicit shared information for each stock

#### 2. Hidden Concept Module (Implicit)

Discovers **latent relationships** not captured by predefined concepts:

```
Learned hidden concepts might capture:
- "Growth stocks" (high P/E, high volatility)
- "Momentum stocks" (recent strong performance)
- "Value stocks" (low P/B, stable earnings)
- "Sentiment-driven stocks" (social media mentions)

HIST finds these automatically from data!
```

**Process**:
1. Remove explicit shared info from stock features
2. Find similar stocks using cosine similarity
3. Group stocks into hidden concepts
4. Extract implicit shared information

#### 3. Individual Information Module

Captures **stock-specific idiosyncratic patterns**:

```
Individual info = Stock features - Explicit - Implicit

Examples:
- Apple's unique product launch cycles
- Tesla's Elon Musk tweets impact
- Small-cap stock-specific volatility
```

### Final Prediction

```python
prediction = w1 * explicit_shared
           + w2 * implicit_shared
           + w3 * individual

# Weights learned during training
```

---

## Why HIST is Better for Rank IC

### XGBoost vs HIST for Ranking

**XGBoost**:
```
Day 1:
  AAPL features → Predict 0.02 (independent)
  MSFT features → Predict 0.01 (independent)

Ranking: AAPL > MSFT

Problem: No guarantee ranking is consistent!
- Next day: MSFT > AAPL (unstable)
- Rank IC → 0
```

**HIST**:
```
Day 1:
  AAPL: explicit=0.015, implicit=0.005, individual=0.003 → 0.023
  MSFT: explicit=0.015, implicit=0.004, individual=-0.001 → 0.018

Ranking: AAPL > MSFT

Advantage: Shared concepts provide stability!
- Both get same Tech sector boost (explicit=0.015)
- Individual differences determine ranking
- More consistent ranking across days → Higher Rank IC
```

### Why HIST Works with Limited Data

**Sample efficiency through concept sharing**:

```
XGBoost needs to learn:
- AAPL patterns (independently)
- MSFT patterns (independently)
- GOOGL patterns (independently)
→ 3000 stocks × 120 days = Need lots of data per stock

HIST learns:
- Tech sector patterns (shared across 500 tech stocks)
- Finance sector patterns (shared across 300 banks)
- Hidden concepts (shared across similar stocks)
→ Concepts learned from ALL stocks simultaneously
→ More efficient use of limited data!
```

**Effective training samples**:
```
XGBoost: 120 days × 1 stock = 120 samples per stock
HIST: 120 days × 500 tech stocks = 60K samples for Tech concept!

→ HIST can learn ranking patterns from concept-level data
→ Works better with 120 days
```

---

## HIST Benchmark Performance

From qlib benchmarks (CSI300, 2017-2020):

| Model | IC | ICIR | **Rank IC** | **Rank ICIR** | Annual Return |
|-------|-----|------|-------------|---------------|---------------|
| Linear | 0.0398 | 0.3155 | 0.0432 | 0.3637 | 10.03% |
| LightGBM | 0.0477 | 0.3644 | 0.0471 | 0.3801 | 13.17% |
| XGBoost | 0.0498 | 0.3779 | 0.0505 | 0.4131 | 14.03% |
| **HIST** | **0.0512** | **0.4219** | **0.0667** | **0.5743** | **16.64%** |

**Key observation**:
- HIST has **32% higher Rank IC** than XGBoost (0.0667 vs 0.0505)
- HIST has **39% higher Rank ICIR** than XGBoost (0.5743 vs 0.4131)
- This is exactly what we need!

---

## Technical Details

### Input Requirements

1. **Features**: Alpha360 (360 features) or Alpha158 (158 features)
   - HIST was benchmarked with Alpha360
   - Uses temporal sequences (60 days of history)

2. **Stock2Concept Matrix**: Maps stocks to predefined concepts
   ```python
   # Shape: [N_stocks, N_concepts]
   # CSI300 uses: sectors, industries, market cap groups
   stock2concept.shape = (300, 83)  # 300 stocks, 83 concepts
   ```

3. **Stock Index**: Maps stock symbols to integer IDs
   ```python
   stock_index = {
       'AAPL': 0,
       'MSFT': 1,
       'GOOGL': 2,
       ...
   }
   ```

### Model Parameters

**From benchmark config**:
```yaml
d_feat: 6           # Feature dimension (Alpha360 has 6 feature groups)
hidden_size: 64     # RNN hidden state size
num_layers: 2       # Number of RNN layers
dropout: 0          # Dropout rate
n_epochs: 200       # Training epochs
lr: 1e-4            # Learning rate (0.0001)
early_stop: 20      # Stop if no improvement for 20 epochs
base_model: LSTM    # Can be LSTM or GRU
```

### Preprocessing Differences

**HIST uses different preprocessing than XGBoost**:

```yaml
infer_processors:
  - RobustZScoreNorm  # Robust normalization (not ZScoreNorm!)
  - Fillna

learn_processors:
  - DropnaLabel
  - CSRankNorm        # Rank normalization (not CSZScoreNorm!)
```

**Key difference**: CSRankNorm converts labels to ranks (0-1 scale)
- This explicitly optimizes for ranking!
- XGBoost uses CSZScoreNorm (Z-score)

---

## Advantages vs XGBoost

| Aspect | XGBoost | HIST |
|--------|---------|------|
| **Ranking ability** | Weak (0.05 Rank IC) | Strong (0.067 Rank IC) |
| **Cross-sectional modeling** | No | Yes (explicit) |
| **Sample efficiency** | Low (needs lots of data) | High (shares via concepts) |
| **Training time** | Fast (5 min) | Slower (30-60 min) |
| **Interpretability** | High (feature importance) | Medium (concept attention) |
| **Requires GPU** | No | Yes (recommended) |
| **Domain knowledge** | Not needed | Need stock2concept matrix |

---

## Disadvantages / Limitations

### 1. Requires Stock-to-Concept Mapping

You need to create or obtain:
- **stock2concept matrix**: Which sector/industry each stock belongs to
- For US stocks (liquid_stocks): Need to build this ourselves

**Options**:
- Use GICS sectors (11 sectors)
- Use GICS industries (24 industry groups)
- Add market cap groups (large/mid/small)
- Add style factors (value/growth/momentum)

### 2. Requires PyTorch

```bash
# XGBoost: Pure CPU, fast
uv pip install xgboost

# HIST: Needs PyTorch + GPU for reasonable speed
uv pip install torch
```

Training time:
- XGBoost: ~5 minutes (CPU)
- HIST: ~30-60 minutes (GPU) or ~3-5 hours (CPU)

### 3. More Complex Setup

**XGBoost**: Just features + labels ✓
**HIST**: Features + labels + stock2concept + stock_index + pretrained LSTM

### 4. Different Feature Format

HIST expects **temporal sequences**:
```
XGBoost: [N_samples, N_features]
         Each sample = 1 day of features

HIST: [N_samples, N_timesteps, N_features_per_timestep]
      Each sample = 60 days of feature history
```

Requires different data handler (Alpha360 instead of Alpha158).

---

## Summary: Should You Use HIST?

### ✅ Use HIST if:

1. **You need better Rank IC** (TopK strategy requires ranking)
2. **You have limited training data** (120 days is OK for HIST)
3. **You have access to GPU** (or patience for CPU training)
4. **You can create stock2concept matrix** (sectors/industries)

### ❌ Stick with XGBoost if:

1. **You only care about IC, not Rank IC**
2. **You need fast iteration** (XGBoost trains in 5 min)
3. **You need interpretability** (feature importance)
4. **No GPU available** and want fast training

---

## Next Steps to Try HIST

1. **Install PyTorch**: `uv pip install torch`
2. **Create stock2concept matrix** for liquid_stocks
   - Map to GICS sectors/industries
   - Save as .npy file
3. **Create stock_index mapping**
4. **Optional: Pretrain LSTM/GRU** (or use random init)
5. **Modify config** to use Alpha360 features (not Alpha158)
6. **Run training** (expect 30-60 min on GPU, 3-5 hours on CPU)

**Expected result**:
- Rank IC: 0 → 0.02-0.04 (with 120 days of data)
- Better ranking consistency
- TopK strategy actually works!

---

## Technical Paper Summary

**Key Innovation**: Decompose stock behavior into:
1. **Explicit shared** (sector/industry effects) - stable across time
2. **Implicit shared** (latent factors) - learned automatically
3. **Individual** (stock-specific) - idiosyncratic

**Why it works**: Ranking requires understanding **relative relationships**, not just individual predictions. By modeling shared concepts, HIST learns which stocks move together and which diverge → Better ranking.

**Mathematical formulation**:
```
Stock_i = α × Explicit_Concept_i
        + β × Implicit_Concept_i
        + γ × Individual_i

Where concepts are shared across stocks,
providing cross-sectional stability.
```

This explicit modeling of cross-sectional structure is why HIST achieves 32% higher Rank IC than XGBoost.
