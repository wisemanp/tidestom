from django.db import migrations

def add_released_tag(apps, schema_editor):
    Tag = apps.get_model('custom_code', 'Tag')
    Tag.objects.get_or_create(name='released', defaults={'description': 'Classifications released to public'})

class Migration(migrations.Migration):

    dependencies = [
        ('custom_code', '0003_humanclassification_pipelineclassificationdash_and_more'),
    ]

    operations = [
        migrations.RunPython(add_released_tag, reverse_code=migrations.RunPython.noop),
    ]
