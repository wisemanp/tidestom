from typing import Required
from django import forms
from django.db import DatabaseError
from django.conf import settings
from .models import TidesClass, TidesClassSubClass, TidesTarget
import os

class TidesTargetForm(forms.Form):
    tidesclass = forms.ChoiceField(label='TiDES Classification')
    tidesclass_other = forms.CharField(
        label='TiDES Classification (Other)',
        required=False
    )
    tidesclass_subclass = forms.ModelChoiceField(
        label='TiDES Sub-classification',
        queryset=TidesClassSubClass.objects.none(),
        required=False
    )
    sn_z = forms.FloatField(required=False, min_value=0.0, label="Redshift (SN)")
    host_z = forms.FloatField(required=False, min_value=0.0, label="Redshift (Host)")
    phase = forms.FloatField(required=False, label="Phase (days)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate main class choices from DB; fallback to static choices on the model if DB is empty
        try:
            db_choices = list(TidesClass.objects.order_by('name').values_list('name', 'name'))
            db_choices.insert(0, (None, '----'))
        except DatabaseError:
            db_choices = []
        fallback = getattr(TidesTarget, 'TIDES_CLASS_CHOICES', [])
        fallback.insert(0, (None, '----'))
        self.fields['tidesclass'].choices = db_choices if db_choices else fallback

        # Dynamically filter subclasses based on selected main class
        main_class_name = None
        if 'tidesclass' in self.data:
            main_class_name = self.data.get('tidesclass')
        elif self.initial.get('tidesclass'):
            main_class_name = self.initial.get('tidesclass')

        if main_class_name:
            try:
                main_class = TidesClass.objects.get(name=main_class_name)
                self.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.filter(main_class=main_class)
            except (TidesClass.DoesNotExist, DatabaseError):
                self.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.none()

    def clean(self):
        cleaned = super().clean()
        tidesclass = cleaned.get('tidesclass')
        tidesclass_other = cleaned.get('tidesclass_other')
        subclass = cleaned.get('tidesclass_subclass')

        # Require "other" text if main class is Other
        if tidesclass == 'Other' and not tidesclass_other:
            self.add_error('tidesclass_other', 'This field is required when "Other" is selected.')

        # Ensure selected subclass belongs to the selected main class
        if subclass and tidesclass and getattr(subclass.main_class, 'name', None) != tidesclass:
            self.add_error('tidesclass_subclass', 'Selected sub-class does not belong to the chosen main class.')

        return cleaned
#TODO Note that at some point we will need to align these choices with the TidesClass and TidesClassSubClass data model
USE_CHOICES=[
    ('Ia', 'Ia'),
    ('Ib', 'Ib'),
    ('Ic', 'Ic'),
    ('II', 'II'),
    ('NotSN', 'NotSN'),
]

def load_subtypes():
    path = os.path.join('/snid_api_runs', "snid_template_options", "subtypes.txt")
    try:
        with open(path) as f:
            subtypes = [line.strip() for line in f if line.strip()]
        return [(s, s) for s in subtypes]
    except FileNotFoundError:
        return []

class SnidParamsForm(forms.Form):
    spectrum = forms.CharField(required=True)
    wmin = forms.FloatField(initial=4000, required=True)
    wmax = forms.FloatField(initial=9000, required=True)
    zmin = forms.FloatField(initial=0.1, required=False)
    zmax = forms.FloatField(initial=1.2, required=False)
    zfix = forms.FloatField(initial=1.0, required=False)
    emclip = forms.FloatField(required=False)
    emwid = forms.IntegerField(required=True, initial=40)
    agemin = forms.IntegerField(required=True, initial=-90)
    agemax = forms.IntegerField(required=True, initial=1000)
    aband = forms.BooleanField(required=False)


    # Multi-selects as MultipleChoiceField
    use = forms.MultipleChoiceField(
        choices=USE_CHOICES, required=False
    )
    usesub = forms.MultipleChoiceField(
        choices=load_subtypes(), required=False
    )
    avoid = forms.MultipleChoiceField(
        choices=USE_CHOICES, required=False
    )
    avoidsub = forms.MultipleChoiceField(
        choices=load_subtypes(), required=False
    )

class NGSFParamsForm(forms.Form):
    spectrum = forms.CharField(required=True)
    z = forms.FloatField(initial=0.0, required=True)
    z_min = forms.FloatField(initial=0.0, required=True)
    z_max = forms.FloatField(initial=0.1, required=True)
    z_int = forms.FloatField(initial=0.01, required=True)
    resolution = forms.FloatField(initial=10, required=True)
    lower_lam = forms.FloatField(initial=0.00, required=True)
    upper_lam = forms.FloatField(initial=0.0, required=True)
    mask_galaxy = forms.BooleanField(required=False)
    mask_telluric = forms.BooleanField(required=False)
    epoch_high = forms.IntegerField(initial=0, required=True)
    epoch_low = forms.IntegerField(initial=0, required=True)
    alam_high = forms.FloatField(initial=2, required=True)
    alam_low = forms.FloatField(initial=-2, required=True)
    alam_interval = forms.FloatField(initial=0.2, required=True)
