from django.db import migrations, models
from django.conf import settings

SEED_TAGS = [
    "auto classification ok",
    "auto classification bad",
    "human classification ok",
    "human classification unsure",
    "high-redshift",
    "noise",
    "galactic",
]

def seed_tags(apps, schema_editor):
    Tag = apps.get_model('custom_code', 'Tag')
    for name in SEED_TAGS:
        Tag.objects.get_or_create(name=name)

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name'], 'db_table': 'tides_tag'},
        ),
        migrations.CreateModel(
            name='TagProposal',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('justification', models.TextField()),
                ('status', models.CharField(max_length=16, choices=[('open','Open'),('accepted','Accepted'),('rejected','Rejected')], default='open')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('proposed_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={'ordering': ['-created'], 'db_table': 'tides_tag_proposal'},
        ),
        migrations.CreateModel(
            name='TargetTag',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                # DB column only; no FK yet to avoid resolution issues
                ('tides', models.BigIntegerField(db_column='tides_id')),
                ('tag', models.ForeignKey(to='custom_code.tag', on_delete=models.CASCADE, related_name='target_tags')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)),
            ],
            options={'db_table': 'tides_target_tag', 'ordering': ['-created']},
        ),
        migrations.AddConstraint(
            model_name='targettag',
            constraint=models.UniqueConstraint(fields=('tides', 'tag'), name='unique_tides_tag'),
        ),
        migrations.RunPython(seed_tags, reverse_code=migrations.RunPython.noop),
    ]