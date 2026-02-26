from django.db import migrations


def cleanup_duplicate_tags(apps, schema_editor):
    """
    Remove duplicate tags and ensure system tags exist.
    """
    Tag = apps.get_model('custom_code', 'Tag')
    TargetTag = apps.get_model('custom_code', 'TargetTag')
    
    # Map of duplicates to canonical names
    duplicates_map = {
        'auto-class-ok': 'auto classification ok',
        'auto-class-bad': None,  # Delete this one
        'human-class-ok': 'human classification ok',
        'human-class-unsure': 'human classification unsure',
        'human classifcation unsure': 'human classification unsure',  # typo
    }
    
    # Merge duplicates into canonical tags
    for old_name, canonical_name in duplicates_map.items():
        old_tag = Tag.objects.filter(name=old_name).first()
        if not old_tag:
            continue
        
        if canonical_name:
            # Merge into canonical
            canonical_tag, _ = Tag.objects.get_or_create(
                name=canonical_name,
                defaults={'is_active': True, 'is_clickable': True}
            )
            # Move all target associations
            TargetTag.objects.filter(tag=old_tag).update(tag=canonical_tag)
        
        # Delete the duplicate
        old_tag.delete()
    
    # Ensure all system tags exist with correct flags
    system_tags = [
        {
            'name': 'released',
            'description': 'Target has been publicly released',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        },
        {
            'name': 'needs-review',
            'description': 'Target requires human review before release',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        },
        {
            'name': 'ready',
            'description': 'Target has been reviewed and approved for release',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        },
    ]
    
    for tag_data in system_tags:
        Tag.objects.update_or_create(
            name=tag_data['name'],
            defaults=tag_data
        )


class Migration(migrations.Migration):
    dependencies = [
        ('custom_code', '0005_humanclassification_pipelineclassificationdash_and_more'),
    ]

    operations = [
        migrations.RunPython(cleanup_duplicate_tags, reverse_code=migrations.RunPython.noop),
    ]
