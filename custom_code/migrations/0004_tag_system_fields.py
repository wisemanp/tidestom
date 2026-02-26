# Generated migration for Tag model updates

from django.db import migrations, models


def create_system_tags(apps, schema_editor):
    """Create system tags for release workflow."""
    Tag = apps.get_model('custom_code', 'Tag')
    
    # System tags for release workflow
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
    
    # Update existing tags to set is_system and is_clickable flags
    existing_tags = Tag.objects.filter(name__in=[
        'auto classification ok',
        'human classification ok', 
        'human classification unsure'
    ])
    for tag in existing_tags:
        tag.is_system = False
        tag.is_clickable = True
        tag.save()
    
    # Create new system tags
    for tag_data in system_tags:
        Tag.objects.update_or_create(
            name=tag_data['name'],
            defaults=tag_data
        )


class Migration(migrations.Migration):

    dependencies = [
        ('custom_code', '0003_add_released_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='is_system',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tag',
            name='is_clickable',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(create_system_tags, reverse_code=migrations.RunPython.noop),
    ]
