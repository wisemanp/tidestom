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
                #self.pipeline_classifications_dash.order_by('-probability').only('z', 'probability').first(),
                self.pipeline_classifications_dash.order_by('-probability').only('probability').first(),
                #self.pipeline_classifications_ed.order_by('-probability').only('z', 'probability').first(),
                self.pipeline_classifications_ed.order_by('-probability').only('probability').first(),
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

    @property
    def tags(self):
        # Returns a queryset so templates can call .all
        return Tag.objects.filter(target_tags__tides_id=self.pk, is_active=True)

    @property
    def latest_auto_classification(self):
        return self.pipeline_classifications_global.order_by('-id').first()

    @property
    def latest_human_classification(self):
        return self.human_classifications.order_by('-created').first()

    @property
    def classifications_agree(self):
        """
        True  - human classification exists and agrees with auto (type + z within 5%).
        False - no human classification, or a disagreement was detected.
        None  - no auto classification to compare against.
        """
        human = self.latest_human_classification
        if not human:
            return False
        auto = self.latest_auto_classification
        if not auto:
            return None
        if auto.sn_type and human.sn_type:
            if auto.sn_type != human.sn_type:
                return False
        if auto.z and human.sn_z:
            z_diff = abs(auto.z - human.sn_z)
            z_percent = (z_diff / max(auto.z, human.sn_z)) * 100
            if z_percent > 5:
                return False
        return True

    def sync_review_tag(self):
        """
        Evaluate the current state of this target and ensure exactly one of
        'needs-review' or 'ready' is set. Returns True if ready, False if
        needs-review. Manual ready/needs-review tags always take precedence;
        'auto classification ok' promotes to ready; classification agreement
        is the final fallback.
        """
        from custom_code.services import get_needs_review_tag, get_ready_tag
        needs_review_tag = get_needs_review_tag()
        ready_tag = get_ready_tag()
        existing = set(self.target_tags.values_list('tag__name', flat=True))

        if ready_tag.name in existing:
            TargetTag.objects.filter(tides=self, tag=needs_review_tag).delete()
            return True

        if needs_review_tag.name in existing:
            return False

        if 'auto classification ok' in existing:
            TargetTag.objects.get_or_create(tides=self, tag=ready_tag, defaults={'user': None})
            TargetTag.objects.filter(tides=self, tag=needs_review_tag).delete()
            return True

        if self.classifications_agree:
            TargetTag.objects.get_or_create(tides=self, tag=ready_tag, defaults={'user': None})
            TargetTag.objects.filter(tides=self, tag=needs_review_tag).delete()
            return True

        # Default: needs review
        TargetTag.objects.get_or_create(tides=self, tag=needs_review_tag, defaults={'user': None})
        TargetTag.objects.filter(tides=self, tag=ready_tag).delete()
        return False

# ----------------------------
# Tags (managed locally)
# ----------------------------
class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)  # System tags cannot be deleted/edited by users
    is_clickable = models.BooleanField(default=True)  # If False, users cannot manually toggle this tag

    class Meta:
        ordering = ['name']
        db_table = 'tides_tag'

    def __str__(self):
        return self.name

class TargetTag(models.Model):
    tides = models.ForeignKey(
        TomTarget,                    # IMPORTANT: reference the class, not 'tom_targets.target'
        on_delete=models.CASCADE,
        db_column='tides_id',
        related_name='target_tags',
    )
    tag = models.ForeignKey('custom_code.Tag', on_delete=models.CASCADE, related_name='target_tags')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tides_target_tag'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(fields=('tides', 'tag'), name='unique_tides_tag'),
        ]

    def __str__(self):
        return f'{self.tides_id} - {self.tag.name}'

class TagProposal(models.Model):
    name = models.CharField(max_length=64)
    justification = models.TextField()
    proposed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=16,
        choices=[('open', 'Open'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='open'
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        db_table = 'tides_tag_proposal'

    def __str__(self):
        return f'{self.name} ({self.status})'

# ----------------------------
# Human classifications (remote)
# ----------------------------
class HumanClassification(models.Model):
    tides_id = models.ForeignKey(
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
    tides_specid = models.BigIntegerField(null=True, blank=True, db_column='tides_specid', db_index=True, unique=True)
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
        indexes = [
            models.Index(fields=['tides_specid'], name='idx_pclass_global_specid'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['tides_specid'], name='pipeline_classification_global_tides_specid_key'),
        ]


class PipelineClassificationSuperfit(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_superfit',
        db_column='tides_id'
    )
    tides_specid = models.BigIntegerField(null=True, blank=True, db_column='tides_specid', db_index=True)
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    z = models.FloatField(null=True, blank=False)

    class Meta:
        managed = False
        db_table = 'pipeline_classification_superfit'
        ordering = ['-probability']
        indexes = [
            models.Index(fields=['tides_specid'], name='idx_pclass_superfit_specid'),
        ]


class PipelineClassificationSnid(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_snid',
        db_column='tides_id'
    )
    tides_specid = models.BigIntegerField(null=True, blank=True, db_column='tides_specid', db_index=True)
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    phase = models.FloatField(null=True, blank=True)
    z = models.FloatField(null=True, blank=True)
    zerr = models.FloatField(null=True, blank=True)
    results_file = models.TextField(null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'pipeline_classification_snid'
        ordering = ['-probability']
        indexes = [
            models.Index(fields=['tides_specid'], name='idx_pclass_snid_specid'),
        ]


class PipelineClassificationDash(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_dash',
        db_column='tides_id'
    )
    tides_specid = models.BigIntegerField(null=True, blank=True, db_column='tides_specid', db_index=True)
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    z = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pipeline_classification_dash'
        ordering = ['-probability']
        indexes = [
            models.Index(fields=['tides_specid'], name='idx_pclass_dash_specid'),
        ]


class PipelineClassificationEd(models.Model):
    tides = models.ForeignKey(
        TidesTarget, on_delete=models.CASCADE,
        related_name='pipeline_classifications_ed',
        db_column='tides_id'
    )
    tides_specid = models.BigIntegerField(null=True, blank=True, db_column='tides_specid', db_index=True)
    sn_type = models.CharField(max_length=50, null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pipeline_classification_ed'
        ordering = ['-probability']
        indexes = [
            models.Index(fields=['tides_specid'], name='idx_pclass_ed_specid'),
        ]


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
    # qmost_id removed - now using tides_specid as PRIMARY KEY
    tides_specid = models.BigIntegerField(primary_key=True, db_column='tides_specid')
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

# Signal to auto-tag new spectra as staged
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='custom_code.TargetTag')
def sync_review_status_on_tag_add(sender, instance, created, **kwargs):
    """
    When 'auto classification ok' is added → promote to ready, clear needs-review.
    When 'auto classification bad' is added → force needs-review, clear ready.
    """
    if not created:
        return

    tag_name = instance.tag.name
    if tag_name not in ('auto classification ok', 'auto classification bad'):
        return

    try:
        from custom_code.services import get_needs_review_tag, get_ready_tag
        target = instance.tides
        needs_review_tag = get_needs_review_tag()
        ready_tag = get_ready_tag()

        if tag_name == 'auto classification ok':
            TargetTag.objects.get_or_create(tides=target, tag=ready_tag, defaults={'user': None})
            TargetTag.objects.filter(tides=target, tag=needs_review_tag).delete()
        elif tag_name == 'auto classification bad':
            TargetTag.objects.get_or_create(tides=target, tag=needs_review_tag, defaults={'user': None})
            TargetTag.objects.filter(tides=target, tag=ready_tag).delete()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f"Failed to sync review status for target {instance.tides_id} on tag '{tag_name}': {e}"
        )


@receiver(post_save, sender=TidesSpec)
def auto_stage_new_spectrum(sender, instance, created, **kwargs):
    """
    When a new spectrum is created, automatically tag its target as 'needs-review'
    if it's not already released or in the queue.
    """
    if not created:
        return
    
    try:
        from custom_code.services import get_needs_review_tag, get_released_tag, get_ready_tag
        
        target = instance.tides
        if not target:
            return
        
        # Check if already released
        released_tag = get_released_tag()
        if target.target_tags.filter(tag=released_tag).exists():
            return
        
        # Check if already in queue (needs-review or ready)
        needs_review_tag = get_needs_review_tag()
        ready_tag = get_ready_tag()
        if target.target_tags.filter(tag__in=[needs_review_tag, ready_tag]).exists():
            return
        
        # Add needs-review tag
        TargetTag.objects.get_or_create(
            tides=target,
            tag=needs_review_tag,
            defaults={'user': None}
        )
    except Exception as e:
        # Don't let tagging errors break spectrum creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to auto-stage target for spectrum {instance.qmost_id}: {e}")