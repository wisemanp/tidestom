from django.db import models
from tom_targets.base_models import BaseTarget

class TidesClass(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class TidesClassSubClass(models.Model):
    main_class = models.ForeignKey(TidesClass, on_delete=models.CASCADE, related_name='sub_classes')
    sub_class = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.main_class.name} - {self.sub_class}"

class TidesTarget(BaseTarget):
    """
    A target with fields defined by a user.
    """
    TIDES_CLASS_CHOICES = [
        ('SN', 'SN'),
        ('SNI','SNI'),
        ('SNIa', 'SNIa'),
        ('SNIbc', 'SNIbc'),
        ('SNIb', 'SNIb'),
        ('SNIc', 'SNIc'),
        ('SNId', 'SNId'),
        ('SNIe', 'SNIe'),
        ('SNII', 'SNII'),
        ('SLSN-I', 'SLSN-I'),
        ('SLSN-II', 'SLSN-II'),
        ('TDE', 'TDE'),
        ('KN', 'KN'),
        ('AGN', 'AGN'),
        ('LRN', 'LRN'),
        ('CV', 'CV'),
        ('LBV', 'LBV'),
        ('Other', 'Other'),
    ]

    tidesclass = models.CharField(max_length=50, choices=TIDES_CLASS_CHOICES, verbose_name='TiDES Classification',default='SN')
    tidesclass_other = models.CharField(max_length=100, blank=True, null=True, verbose_name='TiDES Classification (Other)')
    tidesclass_subclass = models.ForeignKey(TidesClassSubClass, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='TiDES Sub-classification')

    class Meta:
        verbose_name = "target"
        permissions = (
            ('view_target', 'View Target'),
            ('add_target', 'Add Target'),
            ('change_target', 'Change Target'),
            ('delete_target', 'Delete Target'),
        )
