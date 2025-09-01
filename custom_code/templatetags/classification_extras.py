from django import template
from django.shortcuts import get_object_or_404
from ..models import TidesTarget
from ..forms import TidesTargetForm

register = template.Library()


@register.inclusion_tag('custom_code/partials/classification_form.html', takes_context=True)

def classification_form(context, target_id):
	"""
    Renders the human classification submission form for a given target.
    pk == tides_id because TidesTarget uses parent_link to TOM's Target.
    """

	target = get_object_or_404(TidesTarget, id=target_id)
	form = TidesTargetForm()
	return {
		'form': form,
		'target': target,
		'request': context['request']
	}

@register.filter
def divide(value, arg):
	"""Divide value by arg, return float or None if arg=0"""
	try:
		return float(value) / float(arg)
	except (ValueError, ZeroDivisionError, TypeError):
		return None

