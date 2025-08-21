from django import template
from django.shortcuts import get_object_or_404
from ..models import TidesTarget
from ..forms import TidesTargetForm

register = template.Library()

@register.inclusion_tag('custom_code/partials/classification_form.html', takes_context=True)
def classification_form(context, tides_id):
    """
    Renders the human classification submission form for a given target.
    pk == tides_id because TidesTarget uses parent_link to TOM's Target.
    """
    target = get_object_or_404(TidesTarget, pk=tides_id)
    form = TidesTargetForm()
    return {
        'form': form,
        'target': target,
        'request': context['request']
    }