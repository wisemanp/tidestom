from typing import Required
from django import forms
from django.db import DatabaseError
from .models import TidesClass, TidesClassSubClass, TidesTarget

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate main class choices from DB; fallback to static choices on the model if DB is empty
        try:
            db_choices = list(TidesClass.objects.order_by('name').values_list('name', 'name'))
        except DatabaseError:
            db_choices = []
        fallback = getattr(TidesTarget, 'TIDES_CLASS_CHOICES', [])
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

USE_CHOICES=[
    ('type1', 'type1'),
    ('type2', 'type2'),
    ('type3', 'type3'),
    ('type4', 'type4'),
    ('type5', 'type5'),
]

SUBTYPE_CHOICES = [
    ('type1', 'type1'),
    ('type2', 'type2'),
    ('type3', 'type3'),
    ('type4', 'type4'),
    ('type5', 'type5'),
]

class SnidParamsForm(forms.Form):
    wmin = forms.FloatField(initial=4000, required=True)
    wmax = forms.FloatField(initial=9000, required=True)
    zmin = forms.FloatField(initial=0.1, required=True)
    zmax = forms.FloatField(initial=1.2, required=True)
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
        choices=SUBTYPE_CHOICES, required=False
    )
    avoid = forms.MultipleChoiceField(
        choices=USE_CHOICES, required=False
    )
    avoidsub = forms.MultipleChoiceField(
        choices=SUBTYPE_CHOICES, required=False
    )

class NGSFParamsForm(forms.Form):
    z = forms.FloatField(initial=0.1, required=True)
