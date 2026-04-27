# Staging Area and Automated Release System

This system manages the workflow of newly observed targets before they are released to the public.

## Overview

The staging area provides a holding place for newly observed targets to be reviewed before automatic public release. This allows time for:
- Quality checking of automated classifications
- Human review and classification
- Marking agreement/disagreement with automated classifications

## Workflow

1. **New Observations** → Automatically tagged as `staged` when spectra are ingested
2. **Staging Area** → Review page at `/staging/` shows all staged targets with executive summary
3. **Quality Tags** → Users can mark classification quality:
   - `auto-class-ok` - Automated classification is correct
   - `auto-class-bad` - Automated classification is incorrect
   - `human-class-ok` - Human classification is confident
   - `human-class-unsure` - Human classification is uncertain
4. **Automated Release** → Every 24 hours, staged targets are promoted to `released` tag

## Tags

### System Tags (Non-clickable)
- **released** - Target has been released to public
- **staged** - Target is in staging area awaiting release

### Classification Quality Tags (Clickable)
- **auto-class-ok** - Agreement with automated classification
- **auto-class-bad** - Disagreement with automated classification  
- **human-class-ok** - Confident human classification
- **human-class-unsure** - Uncertain human classification

## Usage

### Viewing Staging Area

Navigate to `/staging/` to see:
- Executive summary with statistics
- Table of all staged targets
- Classification details (auto and human)
- Quality tags
- Agreement/disagreement between auto and human classifications

### Manual Release

To manually trigger a release:

```bash
cd /path/to/tidestom
python manage.py release_staged
```

To preview what would be released without actually releasing:

```bash
python manage.py release_staged --dry-run
```

### Automated Release Schedule

Set up a daily cron job to automatically release staged targets. Add to your crontab:

```bash
# Release staged targets daily at 2:00 AM
0 2 * * * cd /Users/pwise/4MOST/tides/tidestom && /path/to/python manage.py release_staged >> /path/to/logs/releases.log 2>&1
```

Or use the provided script:

```bash
# Make the script executable
chmod +x /Users/pwise/4MOST/tides/tidestom/scripts/daily_release.sh

# Add to crontab
crontab -e
# Add line:
0 2 * * * /Users/pwise/4MOST/tides/tidestom/scripts/daily_release.sh
```

## Database Migration

Before using this system, run the migration to add system tag fields:

```bash
python manage.py migrate custom_code 0002_tag_system_fields
```

This will:
1. Add `is_system` and `is_clickable` fields to Tag model
2. Create all system tags (released, staged, classification quality tags)

## Services API

The staging/release system provides these service functions in `custom_code/services.py`:

### `update_staging_area()`
Finds all targets with new observations since last release and tags them as `staged`.
Returns count of newly staged targets.

### `staged_queryset()`
Returns QuerySet of all targets with `staged` tag but not `released` tag.

### `promote_staged_to_released(user=None)`
Moves all staged targets to released by:
- Adding `released` tag
- Removing `staged` tag
Returns count of promoted targets.

## Template Integration

The classification quality tags are automatically displayed on:
- Latest page (`/latest/`)
- Target detail page (`/targets/<id>/`)
- Staging area page (`/staging/`)

Tags appear as colored badges:
- Green: auto-class-ok, human-class-ok
- Red: auto-class-bad
- Orange: human-class-unsure

## Summary Statistics

The staging area provides:
- **Total count** of staged targets
- **Classification distribution** (fractions of each class)
- **Auto vs Human agreement** (count of agreements/disagreements)
- **Redshift range** (min, median, max z values)

## Notes

- The `released` tag is non-clickable - users cannot manually toggle it
- The `staged` tag is also non-clickable - managed by the system
- Classification quality tags are clickable - users can freely toggle them
- System tags cannot be deleted or edited by users
