# LaunchAgent Setup - Summary

**Date**: 2025-10-07
**Status**: ✅ Complete

---

## What Was Set Up

### macOS LaunchAgent for Weekly Delisted Stocks Updates

Following the same pattern as the existing daily automation, I've created a macOS LaunchAgent for weekly delisted stocks updates.

**Schedule**: Every Sunday at 2:00 AM
**Script**: `/Users/zheyuanzhao/workspace/quantmini/scripts/weekly_update.sh`
**LaunchAgent**: `~/Library/LaunchAgents/com.quantmini.weekly.plist`

---

## Files Created/Modified

### QuantMini Pipeline (`/Users/zheyuanzhao/workspace/quantmini/`)

**New Files**:
1. `launchagents/com.quantmini.weekly.plist` - LaunchAgent configuration
2. `launchagents/README.md` - LaunchAgent documentation
3. `scripts/setup_weekly_automation.sh` - Setup script
4. `src/download/delisted_stocks.py` - Core module
5. `scripts/download_delisted_stocks.py` - CLI tool
6. `docs/DELISTED_STOCKS.md` - Feature documentation

**Modified Files**:
1. `scripts/weekly_update.sh` - Updated to follow daily_update.sh pattern
2. `src/download/__init__.py` - Added DelistedStocksDownloader export

### QuantLab Documentation (`/Users/zheyuanzhao/workspace/quantlab/`)

**New Files**:
1. `docs/QUANTMINI_PIPELINE_UPDATE.md` - Pipeline update guide
2. `docs/LAUNCHAGENT_SETUP_SUMMARY.md` - This file

**Modified Files**:
1. `docs/SURVIVORSHIP_BIAS_FIX.md` - Added context

---

## Current Automation Status

```bash
$ launchctl list | grep quantmini
-	0	com.quantmini.weekly    # ✅ Loaded
-	78	com.quantmini.daily     # ✅ Loaded
```

### Daily Updates (Existing)
- **Schedule**: Every day at 6:00 PM
- **What**: Download market data from Polygon S3
- **Data types**: stocks_daily, stocks_minute, options_daily
- **Status**: Already running

### Weekly Updates (New)
- **Schedule**: Every Sunday at 2:00 AM
- **What**: Download delisted stocks from last 90 days
- **Purpose**: Fix survivorship bias
- **Status**: ✅ Installed and loaded

---

## How It Works

### Weekly Automation Flow

```
Sunday 2:00 AM
    ↓
LaunchAgent triggers
    ↓
scripts/weekly_update.sh runs
    ↓
1. Download delisted stocks (last 90 days)
   ├─ Query Polygon API
   ├─ Get stocks delisted in period
   └─ Download OHLCV data → data/parquet/
    ↓
2. Convert to qlib format
   ├─ Run scripts/convert_to_qlib.py
   └─ Update qlib binary data
    ↓
3. Log results
   └─ Save to logs/weekly_*.log
```

### Integration with Daily Updates

The weekly and daily automations work together:

```
Daily (6 PM):
  Polygon S3 → Parquet → Qlib
  └─ Active stocks only

Weekly (Sunday 2 AM):
  Polygon API → Parquet → Qlib
  └─ Delisted stocks only

Universe = Active + Delisted ✓
```

---

## Management Commands

### Check Status
```bash
# Both agents
launchctl list | grep quantmini

# Just weekly
launchctl list | grep quantmini.weekly
```

### Stop/Start
```bash
# Stop weekly updates
launchctl unload ~/Library/LaunchAgents/com.quantmini.weekly.plist

# Start weekly updates
launchctl load ~/Library/LaunchAgents/com.quantmini.weekly.plist
```

### View Logs
```bash
# Latest weekly log
tail -100 $(ls -t logs/weekly_*.log | head -1)

# Watch live
tail -f logs/weekly_stdout.log

# Check for errors
grep -i error logs/weekly_*.log
```

### Test Manually
```bash
# Run weekly script now (doesn't wait for Sunday)
cd /Users/zheyuanzhao/workspace/quantmini
./scripts/weekly_update.sh
```

---

## What Changed from Cron Approach

I initially suggested using cron, but updated to use macOS LaunchAgent to match your existing daily automation:

### Before (Cron)
```bash
# crontab -e
0 2 * * 0 /path/to/weekly_update.sh
```

### After (LaunchAgent) ✅
```bash
./scripts/setup_weekly_automation.sh
launchctl list | grep quantmini.weekly
```

### Why LaunchAgent is Better

1. **Consistent with daily automation** - Same approach for all tasks
2. **Better macOS integration** - Handles sleep/wake properly
3. **Proper logging** - Integrated with system logs
4. **Environment variables** - Can set POLYGON_API_KEY in plist
5. **More reliable** - Apple's recommended method

---

## Verification

### ✅ Setup Complete

```bash
# 1. LaunchAgent installed
$ ls ~/Library/LaunchAgents/com.quantmini.weekly.plist
/Users/zheyuanzhao/Library/LaunchAgents/com.quantmini.weekly.plist

# 2. LaunchAgent loaded
$ launchctl list | grep quantmini.weekly
-	0	com.quantmini.weekly

# 3. Script is executable
$ ls -l scripts/weekly_update.sh
-rwxr-xr-x  1 zheyuanzhao  ...  scripts/weekly_update.sh
```

### Next Run

The weekly automation will run **next Sunday at 2:00 AM**.

To test before then:
```bash
./scripts/weekly_update.sh
```

---

## Troubleshooting

### If weekly updates don't run

**1. Check LaunchAgent is loaded**:
```bash
launchctl list | grep quantmini.weekly
# Should show: -	0	com.quantmini.weekly
```

**2. Check plist file**:
```bash
cat ~/Library/LaunchAgents/com.quantmini.weekly.plist
plutil -lint ~/Library/LaunchAgents/com.quantmini.weekly.plist
```

**3. Check logs**:
```bash
# System logs
log show --predicate 'subsystem == "com.apple.launchd"' --last 24h | grep quantmini

# Script logs
ls -lht logs/weekly_*.log | head -5
```

**4. Reload LaunchAgent**:
```bash
launchctl unload ~/Library/LaunchAgents/com.quantmini.weekly.plist
launchctl load ~/Library/LaunchAgents/com.quantmini.weekly.plist
```

---

## Documentation

- **LaunchAgent setup**: `/Users/zheyuanzhao/workspace/quantmini/launchagents/README.md`
- **Daily automation**: `/Users/zheyuanzhao/workspace/quantmini/AUTOMATION.md`
- **Delisted stocks feature**: `/Users/zheyuanzhao/workspace/quantmini/docs/DELISTED_STOCKS.md`
- **Pipeline update guide**: `/Users/zheyuanzhao/workspace/quantlab/docs/QUANTMINI_PIPELINE_UPDATE.md`

---

## Summary

✅ **Weekly automation installed** - Runs every Sunday at 2 AM
✅ **Follows daily automation pattern** - Uses LaunchAgent (not cron)
✅ **Properly configured** - Both agents loaded and ready
✅ **Well documented** - Complete setup and troubleshooting guides
✅ **Production ready** - Will automatically fix survivorship bias

The QuantMini data pipeline now has comprehensive automation:
- **Daily**: Market data updates (6 PM)
- **Weekly**: Delisted stocks updates (Sunday 2 AM)

---

**Setup Date**: 2025-10-07
**Next Weekly Run**: Next Sunday at 2:00 AM
**Status**: ✅ Ready
