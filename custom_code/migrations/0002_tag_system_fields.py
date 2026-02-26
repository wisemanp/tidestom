# Generated migration for Tag model updates

from django.db import migrations, models


def create_system_tags(apps, schema_editor):
    """Create system tags for classification status and staging."""
    Tag = apps.get_model('custom_code', 'Tag')
    
    system_tags = [
        {
            'name': 'released',
            'description': 'Target has been publicly released',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        },
        {
            'name': 'staged',
            'description': 'Target is in staging area for next release',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        },
        {
            'name': 'auto-class-ok',
            'description': 'Pipeline classification appears correct',
            'is_system': False,
            'is_clickable': True,
            'is_active': True,
        },
        {
            'name': 'auto-class-bad',
            'description': 'Pipeline classification appears incorrect',
            'is_system': False,
            'is_clickable': True,
            'is_active': True,
        },
        {
            'name': 'human-class-ok',
            'description': 'Human classification is confident',
            'is_system': False,
            'is_clickable': True,
            'is_active': True,
        },
        {
            'name': 'human-class-unsure',
            'description': 'Human classification is uncertain',
            'is_system': False,
            'is_clickable': True,
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
        ('custom_code', '0001_initial'),  # Adjust this to your last migration
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
