# Staging Area and Release System - Implementation Summary

## What Was Implemented

This implementation adds a comprehensive staging and release workflow system to TiDES TOM.

### 1. Tag System Enhancements

**Database Changes:**
- Added `is_system` field to Tag model - prevents user modification
- Added `is_clickable` field to Tag model - controls user toggle ability
- Migration creates 6 system tags automatically:
  - `released` (system, non-clickable) - Public released targets
  - `staged` (system, non-clickable) - Targets in staging area
  - `auto-class-ok` (clickable) - Automated classification is correct
  - `auto-class-bad` (clickable) - Automated classification is incorrect
  - `human-class-ok` (clickable) - Human classification is confident
  - `human-class-unsure` (clickable) - Human classification is uncertain

**Files Modified:**
- [custom_code/models.py](tidestom/custom_code/models.py) - Tag model with new fields and auto-staging signal
- [custom_code/migrations/0002_tag_system_fields.py](tidestom/custom_code/migrations/0002_tag_system_fields.py) - Database migration

### 2. Staging Area View

**New Page:** `/staging/`

Shows executive summary of all staged targets with:
- Total count of staged targets
- Classification distribution (fraction of each class)
- Auto vs Human agreement/disagreement counts
- Redshift range (min, median, max)
- Table view of all staged targets with:
  - Target ID (linked)
  - Observation date
  - Auto classification (type, z, probability)
  - Human classification (type, z)
  - Quality tags
  - Agreement indicator

**Files Created:**
- [custom_code/views.py](tidestom/custom_code/views.py#L450-L548) - StagingAreaView class
- [templates/custom_code/staging_area.html](tidestom/templates/custom_code/staging_area.html) - Staging area template

**Files Modified:**
- [tidestom/urls.py](tidestom/tidestom/urls.py) - Added `/staging/` route

### 3. Service Functions

**New functions in [custom_code/services.py](tidestom/custom_code/services.py):**

- `get_staged_tag()` - Get or create the 'staged' system tag
- `staged_queryset()` - Query all staged but not released targets
- `update_staging_area()` - Find and tag new observations as staged
- `promote_staged_to_released(user=None)` - Move staged targets to released

### 4. Automated Release System

**Management Command:**
- [custom_code/management/commands/release_staged.py](tidestom/custom_code/management/commands/release_staged.py)
- Usage: `python manage.py release_staged`
- Supports `--dry-run` flag for testing
- Updates staging area, then promotes staged to released

**Automation Scripts:**
- [scripts/daily_release.sh](tidestom/scripts/daily_release.sh) - Cron-ready shell script
- Handles virtual environment activation
- Logs to `logs/releases.log`
- Example crontab: `0 2 * * * /path/to/daily_release.sh`

### 5. Auto-Staging on Data Ingestion

**Signal Handler:**
- Added `post_save` signal on TidesSpec model
- Automatically tags target as `staged` when new spectrum is created
- Skips if target is already released or staged
- Error handling to prevent ingestion failures

**File Modified:**
- [custom_code/models.py](tidestom/custom_code/models.py#L365-L391) - Added signal receiver

### 6. UI Enhancements

**Classification Quality Tags Display:**
- Updated [custom_code/templates/custom_code/partials/target_classifications.html](tidestom/custom_code/templates/custom_code/partials/target_classifications.html)
- Shows quality tags as colored badges on:
  - Latest page (`/latest/`)
  - Target detail page
  - Staging area page
- Color coding:
  - Green: auto-class-ok, human-class-ok
  - Red: auto-class-bad
  - Orange: human-class-unsure

**Non-Clickable Tags:**
- Updated [custom_code/views.py](tidestom/custom_code/views.py#L259-L288) - ToggleTagView
- Returns 403 error if user tries to toggle non-clickable tag
- Prevents manual toggling of `released` and `staged` tags

### 7. Documentation

**Files Created:**
- [STAGING_AND_RELEASE.md](tidestom/STAGING_AND_RELEASE.md) - Comprehensive user guide
- [IMPLEMENTATION_SUMMARY.md](tidestom/IMPLEMENTATION_SUMMARY.md) - This file

## How to Deploy

### 1. Run Database Migration

```bash
cd /Users/pwise/4MOST/tides/tidestom
python manage.py migrate custom_code 0002_tag_system_fields
```

This will:
- Add is_system and is_clickable columns to custom_code_tag table
- Create all 6 system tags

### 2. Make Release Script Executable

```bash
chmod +x /Users/pwise/4MOST/tides/tidestom/scripts/daily_release.sh
```

### 3. Set Up Cron Job for Daily Releases

```bash
crontab -e
```

Add this line (adjust time as needed):

```cron
# Release staged targets daily at 2:00 AM
0 2 * * * /Users/pwise/4MOST/tides/tidestom/scripts/daily_release.sh
```

### 4. Test the System

**Test staging area view:**
```bash
# Visit in browser:
http://your-tom-url/staging/
```

**Test manual release (dry run):**
```bash
cd /Users/pwise/4MOST/tides/tidestom
python manage.py release_staged --dry-run
```

**Test actual release:**
```bash
python manage.py release_staged
```

## Workflow

### For New Observations

1. Spectrum ingested → Automatically tagged as `staged` (via signal)
2. Target appears in staging area (`/staging/`)
3. Users can review and add quality tags
4. After 24h (or manual trigger), automatically promoted to `released`

### For Users

1. Navigate to `/staging/` to see upcoming releases
2. Review automated classifications
3. Add quality tags to mark agreement/disagreement:
   - Click tag icon next to target
   - Select quality tag (auto-class-ok, auto-class-bad, etc.)
4. Quality tags appear on latest page and target detail pages

### For Administrators

1. Monitor releases: `tail -f logs/releases.log`
2. Manual release: `python manage.py release_staged`
3. Preview releases: `python manage.py release_staged --dry-run`

## Technical Details

### Database Schema Changes

```sql
-- Added to custom_code_tag table:
ALTER TABLE custom_code_tag ADD COLUMN is_system BOOLEAN DEFAULT FALSE;
ALTER TABLE custom_code_tag ADD COLUMN is_clickable BOOLEAN DEFAULT TRUE;
```

### Tag Relationships

```
TidesTarget (1) ←→ (Many) TargetTag (Many) ←→ (1) Tag
                                                     ↓
                                           is_system: bool
                                           is_clickable: bool
```

### Key Functions

```python
# Service functions
get_staged_tag()              # Get staged tag
staged_queryset()             # Query staged targets
update_staging_area()         # Tag new observations
promote_staged_to_released()  # Release staged targets

# Signal
auto_stage_new_spectrum()     # Auto-tag on spectrum save
```

## Files Modified/Created

### Modified Files
1. [custom_code/models.py](tidestom/custom_code/models.py)
   - Added is_system and is_clickable to Tag
   - Added auto-staging signal

2. [custom_code/services.py](tidestom/custom_code/services.py)
   - Added staging/release service functions

3. [custom_code/views.py](tidestom/custom_code/views.py)
   - Added StagingAreaView
   - Updated ToggleTagView to check is_clickable

4. [tidestom/urls.py](tidestom/tidestom/urls.py)
   - Added /staging/ route
   - Imported StagingAreaView

5. [custom_code/templates/custom_code/partials/target_classifications.html](tidestom/custom_code/templates/custom_code/partials/target_classifications.html)
   - Added quality tag display

### Created Files
1. [custom_code/migrations/0002_tag_system_fields.py](tidestom/custom_code/migrations/0002_tag_system_fields.py)
2. [custom_code/management/commands/release_staged.py](tidestom/custom_code/management/commands/release_staged.py)
3. [templates/custom_code/staging_area.html](tidestom/templates/custom_code/staging_area.html)
4. [scripts/daily_release.sh](tidestom/scripts/daily_release.sh)
5. [STAGING_AND_RELEASE.md](tidestom/STAGING_AND_RELEASE.md)
6. [IMPLEMENTATION_SUMMARY.md](tidestom/IMPLEMENTATION_SUMMARY.md)

## Future Enhancements

Possible additions:
- Email notifications when targets are released
- Manual staging area management (remove/add targets)
- Configurable release schedule (not just 24h)
- Quality tag statistics dashboard
- Auto-tagging based on classification agreement thresholds
- Integration with human classification interface
