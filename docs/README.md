# QuantLab Documentation

This directory contains the Sphinx-based documentation for QuantLab.

## Building the Documentation Locally

### Prerequisites

```bash
# Install documentation dependencies
uv add --group dev sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints sphinxcontrib-napoleon
```

### Build HTML Documentation

```bash
cd docs
uv run sphinx-build -b html source build/html
```

Then open `build/html/index.html` in your browser.

### Using Make (Alternative)

```bash
cd docs
make html
```

## ReadTheDocs Setup

This project is configured to automatically build documentation on ReadTheDocs.

### Setup Steps

1. Go to https://readthedocs.org and sign in with GitHub
2. Import the project: https://github.com/nittygritty-zzy/quantlab
3. The configuration in `.readthedocs.yaml` will be used automatically
4. Documentation will be available at: https://quantlab.readthedocs.io

### Configuration Files

- `.readthedocs.yaml` - ReadTheDocs build configuration
- `docs/source/conf.py` - Sphinx configuration
- `docs/Makefile` - Build automation

## Documentation Structure

```
docs/
├── source/
│   ├── index.rst              # Main documentation index
│   ├── installation.rst       # Installation guide
│   ├── quickstart.rst        # Quick start guide
│   ├── cli_overview.rst      # CLI reference
│   ├── user_guide/           # User guides
│   │   ├── visualization.rst
│   │   ├── backtesting.rst
│   │   ├── options.rst
│   │   ├── portfolio.rst
│   │   └── data_management.rst
│   ├── api/                  # API reference (auto-generated)
│   │   ├── core.rst
│   │   ├── data.rst
│   │   ├── visualization.rst
│   │   ├── analysis.rst
│   │   └── cli.rst
│   ├── advanced/             # Advanced topics
│   │   ├── custom_factors.rst
│   │   ├── strategy_development.rst
│   │   ├── performance_optimization.rst
│   │   └── extending_quantlab.rst
│   ├── examples.rst          # Examples
│   ├── faq.rst              # FAQ
│   ├── changelog.rst        # Changelog
│   └── contributing.rst     # Contributing guide
├── build/                    # Generated documentation (git-ignored)
└── Makefile                  # Build automation

```

## Writing Documentation

### Adding New Pages

1. Create a new `.rst` file in the appropriate directory
2. Add it to the `toctree` in the parent index file
3. Rebuild the documentation

### Docstring Format

Use Google-style docstrings for Python code:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short description.

    Longer description with more details about what the
    function does and how to use it.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong

    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        True
    """
    pass
```

### Markdown Support

Markdown files (`.md`) are supported via MyST parser:

```markdown
# My Page Title

Some content with **bold** and *italic*.

- Bullet point 1
- Bullet point 2

\`\`\`python
# Code example
print("Hello, World!")
\`\`\`
```

## Continuous Documentation

Documentation is automatically built and deployed on:

- **ReadTheDocs**: On every push to main branch
- **Pull Requests**: Preview builds for PRs

## Troubleshooting

### Module Import Errors

If autodoc can't find modules, ensure:
1. The project root is in `sys.path` (configured in `conf.py`)
2. All dependencies are installed
3. Module `__init__.py` files exist

### Theme Not Found

Install the theme:
```bash
uv add --group dev sphinx-rtd-theme
```

### Build Warnings

Most warnings are informational. To see detailed errors:
```bash
uv run sphinx-build -W -b html source build/html
```

The `-W` flag treats warnings as errors.

## Contributing

When adding new features to QuantLab:

1. Add docstrings to all public functions/classes
2. Update relevant documentation pages
3. Add examples if applicable
4. Run `make html` to verify docs build correctly

## References

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [ReadTheDocs Guide](https://docs.readthedocs.io/)
- [MyST Parser](https://myst-parser.readthedocs.io/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
