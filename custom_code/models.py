from django.db import models
from django.contrib.auth import get_user_model
from tom_targets.models import Target as TomTarget

User = get_user_model()

class TidesClass(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'tides_class'
        ordering = ['name']


class TidesClassSubClass(models.Model):
    main_class = models.ForeignKey(
        TidesClass, on_delete=models.CASCADE, related_name='sub_classes'
    )
    sub_class = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.main_class.name} - {self.sub_class}"

    class Meta:
        managed = False
        db_table = 'tides_class_subclass'
        unique_together = (('main_class', 'sub_class'),)
        ordering = ['main_class_id', 'sub_class']

# ----------------------------
# Main Target row in tides_cand
# ----------------------------
class TidesTarget(TomTarget):
    target_ptr = models.OneToOneField(
        TomTarget,
        on_delete=models.CASCADE,
        parent_link=True,
        db_column='tides_id',
        primary_key=True,
    )

    lsst_sn_id = models.BigIntegerField(unique=True, null=True, blank=True)
    lsst_host_id = models.BigIntegerField(null=True, blank=True)
    last_date = models.DateTimeField(null=True, blank=True)
    classification = models.CharField(max_length=50, null=True, blank=True)
    z_best = models.FloatField(null=True, blank=True)
    z_sn = models.FloatField(null=True, blank=True)
    z_gal = models.FloatField(null=True, blank=True)
    z_source = models.CharField(max_length=50, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tides_cand'
        verbose_name = 'target'

    # Provide an integer tides_id like your old code expects
    @property
    def tides_id(self):
        return self.pk

    @property
    def human_tidesclass(self):
        rec = self.human_classifications.order_by('-created').only('sn_type').first()
        return rec.sn_type if rec else None

    @property
    def human_tidesclass_subclass(self):
        rec = self.human_classifications.order_by('-created').only('sn_subtype').first()
        return rec.sn_subtype if rec else None

    def add_human_classification(self, *, user: User | None, sn_type: str, sn_subtype: str | None = None,
                                 sn_z: float | None = None, comments: str | None = None, obs_id: int | None = None,
                                 person_id: int | None = None):
        return HumanClassification.objects.create(
            tides=self,
            user=user,
            obs_id=obs_id,
            person_id=person_id,
            sn_type=sn_type,
            sn_z=sn_z,
            sn_subtype=sn_subtype,
            comments=comments,
        )

    @property
    def auto_tidesclass(self):
        g = self.pipeline_classifications_global.order_by('-probability').only('sn_type').first()
        if g:
            return g.sn_type
        best = max(
            [
                self.pipeline_classifications_superfit.order_by('-probability').only('sn_type', 'probability').first(),
                self.pipeline_classifications_snid.order_by('-probability').only('sn_type', 'probability').first(),
                self.pipeline_classifications_dash.order_by('-probability').only('sn_type', 'probability').first(),
                self.pipeline_classifications_ed.order_by('-probability').only('sn_type', 'probability').first(),
            ],
            key=lambda r: (r.probability if r else -1.0),
            default=None,
        )
        return best.sn_type if best else None
    @property
    def auto_tidesclass_z(self):
        g = self.pipeline_classifications_global.order_by('-probability').only('z').first()
        if g:
            return g.z
        best = max(
            [
                self.pipeline_classifications_superfit.order_by('-probability').only('z', 'probability').first(),
                self.pipeline_classifications_snid.order_by('-probability').only('z', 'probability').first(),
                self.pipeline_classifications_dash.order_by('-probability').only('z', 'probability').first(),
                self.pipeline_classifications_ed.order_by('-probability').only('z', 'probability').first(),
            ],
            key=lambda r: (r.probability if r else -1.0),
            default=None,
        )
        return best.z if best else None
    
    @property
    def auto_tidesclass_zerr(self):
        g = self.pipeline_classifications_global.order_by('-probability').only('zerr').first()
        if g:
            return g.zerr
        best = max(
            [
                self.pipeline_classifications_superfit.order_by('-probability').only('zerr', 'probability').first(),
                self.pipeline_classifications_snid.order_by('-probability').only('zerr', 'probability').first(),
                self.pipeline_classifications_dash.order_by('-probability').only('zerr', 'probability').first(),
                self.pipeline_classifications_ed.order_by('-probability').only('zerr', 'probability').first(),
            ],
            key=lambda r: (r.probability if r else -1.0),
            default=None,
        )
        return best.zerr if best else None

    @property
    def auto_tidesclass_prob(self):
        g = self.pipeline_classifications_global.order_by('-probability').only('probability').first()
        if g:
            return g.probability
        best = max(
            [
                self.pipeline_classifications_superfit.order_by('-probability').only('probability').first(),
                self.pipeline_classifications_snid.order_by('-probability').only('probability').first(),
                self.pipeline_classifications_dash.order_by('-probability').only('probability').first(),
                self.pipeline_classifications_ed.order_by('-probability').only('probability').first(),
            ],
            key=lambda r: (r.probability if r else -1.0),
            default=None,
        )
        return best.probability if best else None


# ----------------------------
# Human classifications (remote)
# ----------------------------
class HumanClassification(models.Model):
    tides = models.ForeignKey(
        TidesTarget,
        on_delete=models.CASCADE,
        related_name='human_classifications',
        db_column='tides_id',
    )
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, db_column='person_id'
    )
    obs_id = models.IntegerField(null=True, blank=True)
    sn_type = models.CharField(max_length=50)
    sn_z = models.FloatField(null=True, blank=True)
    phase = models.FloatField(null=True, blank=True)  
    host_z = models.FloatField(null=True, blank=True)  
    sn_subtype = models.CharField(max_length=50, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'human_classifications'
        ordering = ['-created']


# ----------------------------
# Pipeline classifications (remote)
# ----------------------------
class PipelineClassificationGlobal(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_global',
        db_column='tides_id'
    )
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    phase = models.FloatField(null=True, blank=True)
    z = models.FloatField(null=True, blank=True)
    zerr = models.FloatField(null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'pipeline_classification_global'
        ordering = ['-probability']


class PipelineClassificationSuperfit(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_superfit',
        db_column='tides_id'
    )
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pipeline_classification_superfit'
        ordering = ['-probability']


class PipelineClassificationSnid(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_snid',
        db_column='tides_id'
    )
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    phase = models.FloatField(null=True, blank=True)
    z = models.FloatField(null=True, blank=True)
    zerr = models.FloatField(null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'pipeline_classification_snid'
        ordering = ['-probability']


class PipelineClassificationDash(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_dash',
        db_column='tides_id'
    )
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pipeline_classification_dash'
        ordering = ['-probability']


class PipelineClassificationEd(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_ed',
        db_column='tides_id'
    )
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pipeline_classification_ed'
        ordering = ['-probability']


# ----------------------------
# Spectra (remote)
# ----------------------------
class TidesSpec(models.Model):
    tides = models.ForeignKey(
        TidesTarget,
        db_column='tides_id',
        on_delete=models.CASCADE,
        related_name='spectra'
    )
    qmost_id = models.BigIntegerField(primary_key=True)
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    obs_date = models.DateTimeField(null=True, blank=True)
    obs_mjd = models.FloatField(null=True, blank=True)
    snr = models.FloatField(null=True, blank=True)
    seeing = models.FloatField(null=True, blank=True)
    sky_brightness = models.FloatField(null=True, blank=True)
    filepath = models.TextField(null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)
    additional_info = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tides_spec'
        ordering = ['-obs_date']
