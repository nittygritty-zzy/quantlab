# Claude Code Project Instructions

This file is automatically loaded by Claude Code to provide project-specific context.

## Project: QuantLab - Quantitative Trading Research Platform

### CRITICAL: Read Project Memory First
Before making ANY changes, read: `.claude/PROJECT_MEMORY.md`

### Folder Structure - STRICT RULES
- ❌ NO files in project root (except README-level docs)
- ✅ Scripts → `scripts/{data,analysis,tests}/`
- ✅ Docs → `docs/`
- ✅ Configs → `configs/`
- ✅ Results → `results/`

### Quick Reference
- Project overview: `README.md`
- Getting started: `QUICKSTART.md`
- Full structure: `PROJECT_STRUCTURE.md`
- Project memory: `.claude/PROJECT_MEMORY.md` ⭐

### Before Creating Files
1. Check `.claude/PROJECT_MEMORY.md` for rules
2. Determine correct directory (scripts/docs/configs)
3. Use descriptive names (snake_case for scripts)
4. Update documentation if adding major features

### Common Paths
```python
# Always use project-relative paths
configs/lightgbm_liquid_universe.yaml
results/mlruns/[experiment_id]/
docs/BACKTEST_SUMMARY.md
scripts/analysis/visualize_results.py
```

### Data Dependencies
External data: `/Volumes/sandisk/quantmini-data/data/qlib/stocks_daily/`

---
**Remember: Organized structure = Faster development**

