from django import forms
from .models import TidesTarget, TidesClass, TidesClassSubClass

class TidesTargetForm(forms.ModelForm):
    class Meta:
        model = TidesTarget
        fields = ['tidesclass', 'tidesclass_other', 'tidesclass_subclass']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.none()

        if 'tidesclass' in self.data:
            try:
                main_class_name = self.data.get('tidesclass')
                print(f"Trying to get TidesClass with name: {main_class_name}")
                main_class = TidesClass.objects.get(name=main_class_name)
                self.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.filter(main_class=main_class)
            except (ValueError, TypeError, TidesClass.DoesNotExist):
                print(f"TidesClass with name {main_class_name} does not exist.")
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            try:
                main_class_name = self.instance.tidesclass
                print(f"Trying to get TidesClass with name: {main_class_name}")
                main_class = TidesClass.objects.get(name=main_class_name)
                self.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.filter(main_class=main_class)
            except TidesClass.DoesNotExist:
                print(f"TidesClass with name {main_class_name} does not exist.")
                pass  # handle the case where the main class does not exist
    
    def clean(self):
        cleaned_data = super().clean()
        tidesclass = cleaned_data.get('tidesclass')
        tidesclass_other = cleaned_data.get('tidesclass_other')

        if tidesclass == 'Other' and not tidesclass_other:
            self.add_error('tidesclass_other', 'This field is required when "Other" is selected.')

        return cleaned_data