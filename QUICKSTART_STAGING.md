# Quick Start Guide - Staging & Release System

## Deploy in 3 Steps

### Step 1: Run Migration
```bash
cd /Users/pwise/4MOST/tides/tidestom
python manage.py migrate custom_code
```

### Step 2: Make Script Executable
```bash
chmod +x scripts/daily_release.sh
```

### Step 3: Set Up Daily Cron
```bash
crontab -e
# Add this line:
0 2 * * * /Users/pwise/4MOST/tides/tidestom/scripts/daily_release.sh
```

## Quick Test

### View Staging Area
Navigate to: `http://your-tom-url/staging/`

### Manual Release (Dry Run)
```bash
python manage.py release_staged --dry-run
```

### Manual Release (For Real)
```bash
python manage.py release_staged
```

### Check Logs
```bash
tail -f logs/releases.log
```

## What Changed

### New Tags
- **released** 🔒 (non-clickable) - Public released targets
- **staged** 🔒 (non-clickable) - In staging, will be released soon
- **auto-class-ok** ✅ (clickable) - Auto classification correct
- **auto-class-bad** ❌ (clickable) - Auto classification incorrect
- **human-class-ok** ✅ (clickable) - Human confident
- **human-class-unsure** ⚠️ (clickable) - Human uncertain

### New Pages
- `/staging/` - View all staged targets with executive summary

### Automatic Behavior
- New spectra → Auto-tagged as `staged`
- Daily at 2 AM → `staged` becomes `released`

## User Workflow

1. New observation arrives → Goes to staging
2. Review at `/staging/` page
3. Add quality tags if desired (click tag icon on target)
4. Wait 24h → Automatically released
5. OR trigger manual release: `python manage.py release_staged`

## Common Tasks

### Add Quality Tag to Target
1. Go to target detail page
2. Click tag icon
3. Select quality tag (auto-class-ok, auto-class-bad, etc.)

### Check What Will Be Released
```bash
python manage.py release_staged --dry-run
```

### Force Release Now
```bash
python manage.py release_staged
```

### Change Release Time
Edit crontab and change `0 2` to your preferred hour (24h format)

## Troubleshooting

### Migration Fails
Make sure you're in the tidestom directory and using the right Python environment:
```bash
cd /Users/pwise/4MOST/tides/tidestom
source tom_env/bin/activate  # if using venv
python manage.py migrate custom_code
```

### Tags Not Showing
Check if migration ran:
```bash
python manage.py showmigrations custom_code
```

Should show `[X] 0002_tag_system_fields`

### Staging Area Empty
1. Check if any spectra were created recently
2. Check if they're already released: `SELECT * FROM custom_code_targettag WHERE tag_id IN (SELECT id FROM custom_code_tag WHERE name='released');`
3. Manually update staging: Run `python manage.py shell`:
   ```python
   from custom_code.services import update_staging_area
   count = update_staging_area()
   print(f"Staged {count} targets")
   ```

### Cron Not Running
Check cron logs:
```bash
# macOS
log show --predicate 'eventMessage contains "cron"' --last 1h

# Linux
grep CRON /var/log/syslog
```

Check script output:
```bash
cat logs/releases.log
```

## More Details

See full documentation:
- [STAGING_AND_RELEASE.md](STAGING_AND_RELEASE.md) - User guide
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
