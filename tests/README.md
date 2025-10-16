# QuantLab CLI Test Suite

Comprehensive test suite for all QuantLab CLI features.

## Overview

This test suite provides comprehensive coverage for all CLI commands in the QuantLab project. Tests are organized by CLI module and use pytest with mocking to ensure fast, isolated tests.

## Test Structure

```
tests/
├── __init__.py                    # Test package marker
├── README.md                      # This file
├── cli/
│   ├── __init__.py               # CLI tests package marker
│   ├── conftest.py               # Shared fixtures and configuration
│   ├── test_main.py              # Tests for main CLI and init command
│   ├── test_portfolio.py         # Tests for portfolio commands (7 commands)
│   ├── test_data.py              # Tests for data query commands (4 commands)
│   ├── test_analyze.py           # Tests for analysis commands (2 commands)
│   └── test_lookup.py            # Tests for lookup table commands (5 commands)
```

## Commands Covered

### Main CLI (test_main.py)
- **init** - Initialize QuantLab database and configuration

**Total**: 1 command, 11 test cases

### Portfolio Management (test_portfolio.py)
- **create** - Create a new portfolio
- **list** - List all portfolios
- **show** - Show portfolio details and positions
- **delete** - Delete a portfolio
- **add** - Add position(s) to portfolio
- **remove** - Remove position(s) from portfolio
- **update** - Update a position's attributes

**Total**: 7 commands, 38 test cases

### Data Query (test_data.py)
- **check** - Check available Parquet data
- **tickers** - List available tickers
- **query** - Query Parquet data for specific tickers
- **range** - Show date range for Parquet data

**Total**: 4 commands, 21 test cases

### Analysis (test_analyze.py)
- **ticker** - Analyze a single ticker with multi-source data
- **portfolio** - Analyze all tickers in a portfolio

**Total**: 2 commands, 21 test cases

### Lookup Tables (test_lookup.py)
- **init** - Initialize lookup tables
- **stats** - Show lookup table statistics
- **refresh** - Refresh lookup tables (company, ratings, treasury, all)
- **get** - Get data from lookup tables
- **refresh-portfolio** - Refresh lookup tables for portfolio

**Total**: 5 commands, 29 test cases

## Grand Total

**19 CLI commands, 120+ test cases**

## Running Tests

### Run All Tests

```bash
# Using uv (recommended)
uv run pytest tests/

# Using pytest directly
pytest tests/
```

### Run Specific Test Files

```bash
# Test main CLI only
uv run pytest tests/cli/test_main.py

# Test portfolio commands only
uv run pytest tests/cli/test_portfolio.py

# Test data commands only
uv run pytest tests/cli/test_data.py

# Test analyze commands only
uv run pytest tests/cli/test_analyze.py

# Test lookup commands only
uv run pytest tests/cli/test_lookup.py
```

### Run Specific Test Classes

```bash
# Test only portfolio create command
uv run pytest tests/cli/test_portfolio.py::TestPortfolioCreate

# Test only data query command
uv run pytest tests/cli/test_data.py::TestDataQuery

# Test only ticker analysis
uv run pytest tests/cli/test_analyze.py::TestAnalyzeTicker
```

### Run Specific Test Methods

```bash
# Test a specific scenario
uv run pytest tests/cli/test_portfolio.py::TestPortfolioCreate::test_create_portfolio_success

# Test error handling
uv run pytest tests/cli/test_data.py::TestDataQuery::test_query_data_error
```

### Run with Verbose Output

```bash
# Show test names as they run
uv run pytest tests/ -v

# Show all output (including print statements)
uv run pytest tests/ -v -s

# Show test coverage
uv run pytest tests/ --cov=quantlab.cli --cov-report=term-missing
```

### Run with Specific Markers

```bash
# Run only fast tests (if markers are added)
uv run pytest tests/ -m "not slow"

# Run only integration tests
uv run pytest tests/ -m "integration"
```

## Test Fixtures

### Common Fixtures (conftest.py)

All tests have access to these shared fixtures:

- **cli_runner** - Click CLI runner for invoking commands
- **temp_dir** - Temporary directory for test files
- **mock_config_dir** - Mock config directory structure
- **mock_portfolio_data** - Sample portfolio data
- **mock_portfolio_file** - Sample portfolio file
- **mock_parquet_data** - Mock Parquet data
- **mock_lookup_manager** - Mock lookup table manager
- **mock_data_api** - Mock data API
- **patch_config_path** - Patches config directory path
- **patch_data_path** - Patches data directory path
- **isolated_filesystem** - Isolated filesystem for tests
- **sample_analysis_result** - Sample analysis result data
- **reset_env_vars** - Auto-resets environment variables

## Test Categories

### Success Tests
Tests that verify commands work correctly with valid inputs.

Example:
```python
def test_create_portfolio_success(self, cli_runner):
    """Test successful portfolio creation"""
    # Tests that portfolio creation works as expected
```

### Error Handling Tests
Tests that verify commands handle errors gracefully.

Example:
```python
def test_create_portfolio_value_error(self, cli_runner):
    """Test portfolio creation handles ValueError"""
    # Tests that errors are caught and reported properly
```

### Edge Case Tests
Tests that verify commands handle unusual but valid inputs.

Example:
```python
def test_list_portfolios_empty(self, cli_runner):
    """Test listing when no portfolios exist"""
    # Tests behavior with empty data
```

### Integration Tests
Tests that verify multiple commands work together.

Example:
```python
def test_create_and_show_portfolio(self, cli_runner):
    """Test creating portfolio then showing it"""
    # Tests command interaction
```

## Mocking Strategy

All tests use mocking to avoid:
- Database operations
- API calls
- File system modifications
- Network requests

This ensures:
- **Fast tests** - All tests run in < 1 second
- **Isolated tests** - No dependencies between tests
- **Reliable tests** - No external dependencies
- **Safe tests** - No side effects on real data

Example mocking:
```python
def test_analyze_ticker_basic(self, cli_runner):
    # Mock the analyzer
    mock_analyzer = Mock()
    mock_analyzer.analyze_ticker.return_value = {
        "status": "success",
        "ticker": "AAPL",
        "price": {"current": 180.50}
    }

    # Run command with mocked dependencies
    result = cli_runner.invoke(
        analyze,
        ['ticker', 'AAPL'],
        obj={'analyzer': mock_analyzer}
    )

    # Verify behavior
    assert result.exit_code == 0
    assert 'AAPL' in result.output
```

## Code Coverage

Target: **90%+ coverage** for all CLI modules

Run coverage report:
```bash
uv run pytest tests/ --cov=quantlab.cli --cov-report=html
open htmlcov/index.html
```

## Adding New Tests

### When Adding a New CLI Command

1. Add test class in appropriate test file
2. Add success test
3. Add error handling test
4. Add edge case tests
5. Update this README

### Test Template

```python
class TestNewCommand:
    """Tests for 'new-command' command"""

    def test_new_command_success(self, cli_runner):
        """Test successful execution"""
        # Arrange - Setup mocks
        mock_mgr = Mock()
        mock_mgr.new_command.return_value = expected_result

        # Act - Run command
        result = cli_runner.invoke(
            command_group,
            ['new-command', 'arg1', '--option', 'value'],
            obj={'manager': mock_mgr}
        )

        # Assert - Verify results
        assert result.exit_code == 0
        assert 'expected output' in result.output
        mock_mgr.new_command.assert_called_once()

    def test_new_command_error(self, cli_runner):
        """Test error handling"""
        # Test error scenarios
```

## Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** that describe what's being tested
3. **Mock external dependencies** to keep tests fast
4. **Test both success and failure** paths
5. **Use fixtures** to reduce code duplication
6. **Follow AAA pattern**: Arrange, Act, Assert
7. **Keep tests isolated** - no dependencies between tests
8. **Test behavior, not implementation** - focus on outputs

## Continuous Integration

Tests should be run:
- Before each commit
- In CI/CD pipeline
- Before merging pull requests

Example GitHub Actions workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest tests/ --cov=quantlab.cli
```

## Troubleshooting

### Tests Failing

1. **Check mock setup** - Ensure mocks return expected data
2. **Check assertions** - Verify expected values match actual values
3. **Run with -v** - See which specific test is failing
4. **Run with -s** - See print statements and output
5. **Check fixtures** - Ensure fixtures are being used correctly

### Slow Tests

1. **Check for real I/O** - Should use mocks, not real files/DB
2. **Check for sleeps** - Remove any time.sleep() calls
3. **Profile tests** - Use pytest-profiling to find bottlenecks

### Flaky Tests

1. **Check for randomness** - Use fixed seeds
2. **Check for timing issues** - Remove time-dependent logic
3. **Check for state** - Ensure tests don't depend on each other

## Test Metrics

Current status:
- **Total test files**: 6
- **Total test classes**: 24
- **Total test cases**: 120+
- **Coverage**: TBD (run coverage report)
- **Avg test time**: < 0.5s per test

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Click Testing](https://click.palletsprojects.com/en/8.1.x/testing/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Contributing

When contributing tests:
1. Follow existing test structure
2. Use descriptive test names
3. Add docstrings to test methods
4. Update this README if adding new test files
5. Ensure all tests pass before submitting PR

## Questions?

For questions about the test suite, please:
1. Check this README
2. Look at existing tests for examples
3. Ask in project discussions
