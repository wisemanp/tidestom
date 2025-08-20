from django import forms
from .models import TidesTarget, TidesClass, TidesClassSubClass

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
        db_choices = list(TidesClass.objects.order_by('name').values_list('name', 'name'))
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
            except TidesClass.DoesNotExist:
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
        if subclass and tidesclass and subclass.main_class.name != tidesclass:
            self.add_error('tidesclass_subclass', 'Selected sub-class does not belong to the chosen main class.')

        return cleaned