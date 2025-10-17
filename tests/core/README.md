# Core Module Tests

Comprehensive test suite for Phase 3 Enhanced Discovery features.

## Test Coverage

### Unit Tests

#### ScreenExporter (`test_screen_export.py`)
**20 tests covering:**

1. **Result Enrichment (5 tests)**
   - Company info enrichment (name, sector, industry)
   - Calculated fields (% from SMA, BB position)
   - Empty DataFrame handling
   - Missing column handling
   - Column ordering

2. **Excel Export (5 tests)**
   - File creation
   - Enrichment integration
   - Custom sheet names
   - Empty results handling
   - Parent directory creation

3. **CSV Export (3 tests)**
   - File creation
   - Enrichment integration
   - Data integrity verification

4. **Comparison Reports (3 tests)**
   - Multi-sheet creation
   - Sector aggregation
   - Empty results handling

5. **Edge Cases (4 tests)**
   - Missing optional columns
   - Unknown tickers
   - NA value handling
   - File permissions

#### WatchlistManager (`test_watchlist.py`)
**29 tests covering:**

1. **Watchlist Creation (3 tests)**
   - Basic creation
   - Metadata (description, tags)
   - Duplicate prevention

2. **Watchlist Listing (5 tests)**
   - Empty list
   - Multiple watchlists
   - Stock counts
   - Content retrieval
   - Nonexistent watchlist

3. **Adding Screen Results (5 tests)**
   - Basic addition
   - Replace mode (default)
   - Merge mode
   - Metadata preservation
   - Nonexistent watchlist handling

4. **Snapshot Tracking (4 tests)**
   - Automatic snapshot creation
   - Change detection
   - Price change calculation
   - Insufficient data handling

5. **Watchlist Deletion (3 tests)**
   - Basic deletion
   - Item removal
   - Nonexistent watchlist

6. **Export Functionality (2 tests)**
   - JSON export
   - Nonexistent watchlist

7. **Alerts (2 tests)**
   - Single alert creation
   - Multiple alerts

8. **Edge Cases (5 tests)**
   - Empty DataFrame
   - Missing price column
   - Missing score column
   - Long watchlist ID
   - Special characters in name

### Integration Tests

#### Phase 3 Integration (`test_phase3_integration.py`)
**Tests covering end-to-end workflows:**

1. **Sector/Industry Screening**
   - Screen by sector
   - Exclude sectors
   - Screen by industry

2. **Export Workflow**
   - Screen → Excel export
   - Screen → CSV export
   - Multi-sheet comparison reports

3. **Watchlist Workflow**
   - Screen → watchlist → retrieve
   - Snapshot comparison over time
   - Watchlist export

4. **End-to-End Scenarios**
   - Complete discovery workflow
   - Multi-criteria screening with export

5. **Error Handling**
   - Invalid sector handling
   - Empty results export
   - Missing data in watchlists

## Running Tests

### All Phase 3 Tests
```bash
uv run pytest tests/core/ -v
```

### Specific Test Files
```bash
# ScreenExporter tests
uv run pytest tests/core/test_screen_export.py -v

# WatchlistManager tests
uv run pytest tests/core/test_watchlist.py -v

# Integration tests
uv run pytest tests/integration/test_phase3_integration.py -v
```

### With Coverage
```bash
uv run pytest tests/core/ --cov=quantlab.core.screen_export --cov=quantlab.core.watchlist --cov-report=html
```

## Test Results

### Latest Run
- **Unit Tests**: 49/49 passed (100%)
  - ScreenExporter: 20/20 passed
  - WatchlistManager: 29/29 passed
- **Duration**: ~0.87s

### Coverage Goals
- Line coverage: >90%
- Branch coverage: >85%
- Critical paths: 100%

## Test Fixtures

### Mock Objects
- `mock_db`: Mock DatabaseManager
- `mock_lookup`: Mock LookupTableManager with sample data
- `mock_parquet_reader`: Mock ParquetReader with test data
- `mock_data_manager`: Mock DataManager with fundamentals

### Sample Data
- `sample_results`: 3-stock screening results (AAPL, MSFT, JPM)
- `sample_screen_results`: Results with price, score, and RSI

### Temporary Resources
- `temp_db`: Temporary DuckDB database
- `tempfile.TemporaryDirectory`: Auto-cleaned temp directories

## Test Data

### Companies
- **AAPL**: Technology / Consumer Electronics
- **MSFT**: Technology / Software
- **JPM**: Financials / Banks

### Fundamentals (Mock)
- Market caps: $2.8T - $3.0T
- P/E ratios: 28.5 - 32.0
- Profit margins: 25% - 35%
- Revenue growth: 8% - 15%

## Best Practices

1. **Isolation**: Each test is independent, uses fixtures
2. **Cleanup**: Temporary files/databases auto-cleaned
3. **Mocking**: External dependencies mocked (APIs, file I/O)
4. **Coverage**: Test happy path, edge cases, and errors
5. **Speed**: Fast execution (<1s for all unit tests)

## Adding New Tests

### Unit Test Template
```python
def test_new_feature(self, exporter, sample_results):
    """Test new feature description"""
    # Arrange
    ...

    # Act
    result = exporter.new_feature(sample_results)

    # Assert
    assert result is not None
    assert expected_condition
```

### Integration Test Template
```python
def test_new_workflow(self, screener, db_manager, lookup_manager):
    """Test complete workflow description"""
    # Setup
    ...

    # Execute workflow steps
    ...

    # Verify end result
    assert final_condition
```

## CI/CD Integration

### Pre-commit Hook
```bash
#!/bin/bash
uv run pytest tests/core/ --tb=short
```

### GitHub Actions
```yaml
- name: Run Phase 3 Tests
  run: |
    uv run pytest tests/core/ -v --cov --cov-report=xml
```

## Troubleshooting

### Common Issues

1. **DuckDB import errors**
   - Solution: Ensure `conftest.py` pre-imports DuckDB

2. **Temporary file cleanup**
   - Solution: Use `tempfile.TemporaryDirectory()` context manager

3. **Mock data updates**
   - Solution: Update fixtures in conftest or test file

4. **Slow tests**
   - Solution: Check for unmocked API calls or large datasets

## Related Documentation

- [ScreenExporter API](../../quantlab/core/screen_export.py)
- [WatchlistManager API](../../quantlab/core/watchlist.py)
- [Integration Test Guide](../integration/README.md)
