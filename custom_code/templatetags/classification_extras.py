from django import template
from django.shortcuts import get_object_or_404
from ..models import MirroredTidesTarget
from ..forms import TidesTargetForm

register = template.Library()

@register.inclusion_tag('custom_code/partials/classification_form.html', takes_context=True)
def classification_form(context, tides_id):
    """
    Renders the human classification submission form for a given target.
    """
    target = get_object_or_404(MirroredTidesTarget, tides_id=tides_id)
    form = TidesTargetForm()
    return {
        'form': form,
        'target': target,
        'request': context['request']
    }