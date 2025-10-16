# Integration Tests

Integration tests for QuantLab CLI using **real components** (no mocking).

## Overview

Unlike unit tests which use mocks, integration tests:
- ✅ Use **real databases** (temporary SQLite)
- ✅ Use **real file systems** (temporary directories)
- ✅ Test **actual component interactions**
- ✅ Verify **data persistence**
- ❌ **Do NOT mock** dependencies

## Test Structure

```
tests/integration/
├── __init__.py
├── README.md (this file)
├── conftest.py                      # Integration test fixtures
├── test_main_integration.py         # Main CLI & init tests
├── test_portfolio_integration.py    # Portfolio management tests
└── test_data_integration.py         # Data query tests
```

## Running Integration Tests

### Run All Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run with markers
uv run pytest -m integration -v
```

### Run Specific Test Files

```bash
# Portfolio integration tests only
uv run pytest tests/integration/test_portfolio_integration.py -v

# Main CLI integration tests only
uv run pytest tests/integration/test_main_integration.py -v

# Data integration tests only
uv run pytest tests/integration/test_data_integration.py -v
```

### Run Specific Test Classes

```bash
# Test portfolio lifecycle
uv run pytest tests/integration/test_portfolio_integration.py::TestPortfolioIntegration -v

# Test database persistence
uv run pytest tests/integration/test_main_integration.py::TestDatabasePersistence -v
```

## What's Tested

### Portfolio Integration (test_portfolio_integration.py)

**37 tests** covering:

1. **Basic Operations**
   - Create and list portfolios
   - Show portfolio details
   - Delete portfolios

2. **Position Management**
   - Add single/multiple positions
   - Remove positions
   - Update position attributes (weight, shares, cost basis, notes)

3. **Data Persistence**
   - Portfolio data persists across commands
   - Updates persist in database
   - Data survives database reconnection

4. **Error Handling**
   - Non-existent portfolios
   - Invalid position updates
   - Duplicate portfolio IDs

5. **Complex Scenarios**
   - Managing multiple portfolios
   - Position weight calculations
   - Full portfolio lifecycle

### Main CLI Integration (test_main_integration.py)

**Tests** covering:

1. **CLI Basics**
   - Help display
   - Version command
   - Subcommand registration

2. **Init Command**
   - Database schema creation
   - Data availability checks
   - Multiple init runs
   - Next steps guidance

3. **Complete Workflows**
   - Full portfolio workflow (init → create → add → update → delete)
   - Database persistence across reconnections
   - Concurrent-like operations

4. **Database Operations**
   - Table creation verification
   - Data persistence
   - Connection handling

### Data Integration (test_data_integration.py)

**Tests** covering:

1. **Data Commands**
   - Check data availability (empty directory)
   - List tickers (no data)
   - Show date ranges (no data)
   - Query data (no data)

2. **Command Options**
   - Different data types (stocks_daily, stocks_minute, options_daily, options_minute)
   - Date range parameters
   - Limit parameters
   - Multiple tickers

3. **Error Handling**
   - Invalid date formats
   - Missing required arguments

## Key Differences from Unit Tests

| Aspect | Unit Tests | Integration Tests |
|--------|------------|-------------------|
| **Mocking** | Heavy mocking | No mocking |
| **Database** | Mocked DatabaseManager | Real SQLite database |
| **File System** | Mocked paths | Real temporary directories |
| **Speed** | Very fast (< 1s) | Slower (~2-5s) |
| **Scope** | Single component | Multiple components |
| **Purpose** | Verify logic | Verify integration |

## Fixtures

### Core Fixtures (conftest.py)

- **cli_runner** - Click CLI runner
- **temp_dir** - Temporary directory (auto-cleanup)
- **test_db_path** - Path for test database
- **test_parquet_dir** - Directory for parquet data
- **test_config** - Real Config object
- **real_db** - Real DatabaseManager with schema
- **real_parquet_reader** - Real ParquetReader
- **real_portfolio_manager** - Real PortfolioManager
- **sample_portfolio** - Pre-populated portfolio for testing
- **cli_context** - Complete CLI context with real objects

### Automatic Cleanup

All fixtures use `temp_dir` which automatically cleans up after each test:
- Temporary databases are deleted
- Temporary files are removed
- No test artifacts left behind

## Best Practices

### When Writing Integration Tests

1. **Use Real Components**
   ```python
   # ✅ Good - uses real database
   def test_portfolio_creation(cli_runner, real_db):
       pm = PortfolioManager(real_db)
       portfolio = pm.create_portfolio("test", "Test")
       assert portfolio is not None
   ```

   ```python
   # ❌ Bad - uses mocks (use unit tests instead)
   def test_portfolio_creation(cli_runner):
       mock_db = Mock()
       pm = PortfolioManager(mock_db)
       # ...
   ```

2. **Test Data Persistence**
   ```python
   # ✅ Good - verifies data persists
   def test_persistence(cli_runner, cli_context):
       # Create portfolio
       cli_runner.invoke(portfolio, ['create', 'test', '--name', 'Test'])

       # Verify it exists (reads from DB)
       result = cli_runner.invoke(portfolio, ['show', 'test'])
       assert 'Test' in result.output
   ```

3. **Test Real Workflows**
   ```python
   # ✅ Good - tests complete user workflow
   def test_workflow(cli_runner, cli_context):
       # Init
       cli_runner.invoke(init)

       # Create portfolio
       cli_runner.invoke(portfolio, ['create', 'test'])

       # Add position
       cli_runner.invoke(portfolio, ['add', 'test', 'AAPL'])

       # Update position
       cli_runner.invoke(portfolio, ['update', 'test', 'AAPL', '--weight', '0.5'])

       # Verify final state
       result = cli_runner.invoke(portfolio, ['show', 'test'])
       assert '50.00%' in result.output
   ```

4. **Test Error Conditions**
   ```python
   # ✅ Good - tests real error handling
   def test_nonexistent_portfolio(cli_runner, cli_context):
       result = cli_runner.invoke(portfolio, ['show', 'nonexistent'])
       assert '❌ Portfolio not found' in result.output
   ```

### What NOT to Test in Integration Tests

- ❌ API calls to external services (would need API keys)
- ❌ Very slow operations (keep tests under 10 seconds each)
- ❌ Component-level logic (use unit tests)
- ❌ Mock behavior (that's for unit tests)

## Running Specific Scenarios

### Test Portfolio Lifecycle

```bash
uv run pytest tests/integration/test_portfolio_integration.py::TestPortfolioIntegration::test_create_show_and_delete_portfolio -v
```

### Test Database Persistence

```bash
uv run pytest tests/integration/test_main_integration.py::TestDatabasePersistence -v
```

### Test Complete Workflow

```bash
uv run pytest tests/integration/test_main_integration.py::TestCLIWorkflow::test_full_portfolio_workflow -v
```

## Debugging Integration Tests

### See Test Output

```bash
# Show print statements and test output
uv run pytest tests/integration/ -v -s
```

### Run Single Test with Output

```bash
uv run pytest tests/integration/test_portfolio_integration.py::TestPortfolioIntegration::test_add_and_remove_positions -v -s
```

### See Database Contents

```python
def test_debug_database(cli_runner, real_db):
    # Create portfolio
    pm = PortfolioManager(real_db)
    pm.create_portfolio("test", "Test")

    # Inspect database (DuckDB API)
    conn = real_db.conn
    result = conn.execute("SELECT * FROM portfolios")
    print(result.fetchall())  # Run with -s to see output
```

## Continuous Integration

Integration tests should run:
- ✅ Before merging pull requests
- ✅ On main branch after merge
- ✅ Before releases

Example CI configuration:

```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v
```

## Performance

Current performance:
- **Total tests**: ~40+ integration tests
- **Total time**: ~2-5 seconds
- **Per test avg**: ~50-100ms

Integration tests are slower than unit tests but still fast enough to run frequently.

## Troubleshooting

### Tests Fail with Database Locked

**Cause**: Database not being closed properly

**Solution**: Ensure all fixtures properly close connections

### Tests Fail with File Not Found

**Cause**: Incorrect path handling

**Solution**: Use `str()` when passing Path objects to functions expecting strings

### Tests Leave Temp Files

**Cause**: Fixture not cleaning up

**Solution**: All integration tests use `temp_dir` which auto-cleans. If you see leftover files, check fixture usage.

## Adding New Integration Tests

1. **Choose the right file** based on what you're testing
2. **Use appropriate fixtures** (cli_context, real_db, etc.)
3. **Don't use mocks** - use real components
4. **Test complete workflows** - not just individual functions
5. **Verify persistence** - test that data survives across operations
6. **Clean test names** - describe what scenario is being tested

Example template:

```python
class TestNewFeatureIntegration:
    """Integration tests for new feature"""

    def test_complete_workflow(self, cli_runner, cli_context):
        """Test complete new feature workflow"""
        # Setup
        # ... real component initialization

        # Execute
        result = cli_runner.invoke(command, args, obj=cli_context)

        # Verify
        assert result.exit_code == 0
        assert 'expected output' in result.output

        # Verify persistence
        result2 = cli_runner.invoke(verify_command, obj=cli_context)
        assert 'data persisted' in result2.output
```

## Summary

Integration tests provide:
- ✅ **Real component testing** - no mocks
- ✅ **Workflow validation** - complete user scenarios
- ✅ **Database persistence** - data survives operations
- ✅ **Error handling** - real error conditions
- ✅ **Fast execution** - still runs in seconds

Together with unit tests, integration tests ensure QuantLab CLI works correctly in real-world usage!
