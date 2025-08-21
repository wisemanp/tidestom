from django.db import models
from tom_targets.base_models import BaseTarget

from collections import Counter


class TidesCand(models.Model):
    """
    A target model that represents entries in the tides_cand table.
    """
    # Fields matching tides_cand structure
    tides_id = models.BigIntegerField(primary_key=True)  # Matches tides_cand.tides_id
    lsst_sn_id = models.BigIntegerField(unique=True)  # Matches tides_cand.lsst_sn_id
    lsst_host_id = models.BigIntegerField(null=True, blank=True)  # Matches tides_cand.lsst_host_id
    last_date = models.DateTimeField(null=True, blank=True)  # Matches tides_cand.last_date
    classification = models.CharField(max_length=50, null=True, blank=True)  # Matches tides_cand.classification
    z_best = models.FloatField(null=True, blank=True)  # Matches tides_cand.z_best
    z_sn = models.FloatField(null=True, blank=True)  # Matches tides_cand.z_sn
    z_gal = models.FloatField(null=True, blank=True)  # Matches tides_cand.z_gal
    z_source = models.CharField(max_length=50, null=True, blank=True)  # Matches tides_cand.z_source
    confidence = models.FloatField(null=True, blank=True)  # Matches tides_cand.confidence
    class Meta:
        db_table = 'tides_cand'  # Matches the table name in tides_db
        managed = False  # Prevent Django from managing this table
        verbose_name = "backend_tides_target"
        
        app_label = 'custom_code'  # Ensure this model is recognized in the custom_code app
        permissions = (
            ('view_target', 'View Target'),
            ('add_target', 'Add Target'),
            ('change_target', 'Change Target'),
            ('delete_target', 'Delete Target'),
        )

class MirroredTidesTarget(BaseTarget):
    """
    A model that mirrors the TidesTarget structure for use in the main application.
    Inherits from BaseTarget to maintain compatibility with existing target management.
    """
    #type = models.CharField(max_length=100, default='TIDES', editable=False)
    tides_id = models.BigIntegerField(primary_key=True)  # Matches tides_cand.tides_id
    lsst_sn_id = models.BigIntegerField(unique=True)  # Matches tides_cand.lsst_sn_id
    lsst_host_id = models.BigIntegerField(null=True, blank=True)  # Matches tides_cand.lsst_host_id
    last_date = models.DateTimeField(null=True, blank=True)  # Matches tides_cand.last_date
    classification = models.CharField(max_length=50, null=True, blank=True)  # Matches tides_cand.classification
    z_best = models.FloatField(null=True, blank=True)  # Matches tides_cand.z_best
    z_sn = models.FloatField(null=True, blank=True)  # Matches tides_cand.z_sn
    z_gal = models.FloatField(null=True, blank=True)  # Matches tides_cand.z_gal
    z_source = models.CharField(max_length=50, null=True, blank=True)  # Matches tides_cand.z_source
    confidence = models.FloatField(null=True, blank=True)  # Matches tides_cand.confidence

    class Meta:
        managed = True  # Allow Django to manage this table
        verbose_name = "django_target"


class HumanClassification(models.Model):
    tides_id = models.BigIntegerField()
    obs_id = models.IntegerField(null=True, blank=True)
    person_id = models.IntegerField()
    sn_type = models.CharField(max_length=50)
    sn_z = models.FloatField(null=True, blank=True)
    sn_subtype = models.CharField(max_length=100, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    #type = None  # Placeholder for type, not used in this model
    class Meta:
        db_table = 'human_classifications'  # Match the table name in tides_db
        managed = False  # Prevent Django from managing migrations for this table

    @staticmethod
    def aggregate_human_tidesclass(tides_id):
        """
        Aggregate the most common classification for a given tides_id.
        """
        submissions = HumanClassification.objects.filter(tides_id=tides_id)
        if not submissions.exists():
            return None

        # Aggregate the most common classification
        tidesclass_counts = Counter(sub.sn_type for sub in submissions)
        most_common_class, count = tidesclass_counts.most_common(1)[0]

        return {
            'most_common_class': most_common_class,
            'count': count,
            'total_submissions': submissions.count(),
        }

class TidesSpec(models.Model):
    """
    A model representing entries in the tides_spec table.
    This model is read-only and reflects the structure of tides_spec.
    """
    tides_id = models.BigIntegerField()  # Foreign key to tides_cand.tides_id
    qmost_id = models.BigIntegerField(primary_key=True)  # Primary key
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    obs_date = models.DateTimeField(null=True, blank=True)
    obs_mjd = models.FloatField(null=True, blank=True)
    snr = models.FloatField(null=True, blank=True)
    seeing = models.FloatField(null=True, blank=True)
    sky_brightness = models.FloatField(null=True, blank=True)
    filepath = models.TextField(null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)
    additional_info = models.JSONField(null=True, blank=True)
    #type=None # Placeholder for type, not used in this model
    class Meta:
        db_table = 'tides_spec'  # Matches the table name in tides_db
        managed = False  # Prevent Django from managing this table

class PipelineClassificationGlobal(models.Model):
    """
    A model representing entries in the pipeline_classification_global table.
    """
    tides_target = models.ForeignKey(
        'TidesCand',  # Reference the Django model for tides_cand
        on_delete=models.CASCADE,
        related_name='pipeline_classifications'  # Avoid naming conflict
    )
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    #type = None
    class Meta:
        db_table = 'pipeline_classification_global'  # Matches the table name in tides_db
        managed = False  # Prevent Django from managing migrations for this table

    @staticmethod
    def get_auto_classifications(tides_id):
        """
        Get auto-classifications for a given tides_id.
        """
        return PipelineClassificationGlobal.objects.filter(tides_target__tides_id=tides_id).order_by('-probability')
