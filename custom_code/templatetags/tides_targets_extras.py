from django import template
from django.conf import settings
from django.db.models import Count
from custom_code.models import PipelineClassificationGlobal, HumanClassification, PipelineClassificationSnid
from myplots.templatetags.utils import find_target_name

register = template.Library()

@register.inclusion_tag('custom_code/partials/target_data.html')
def tides_target_data(target):
    """
    Render extra target fields from settings.EXTRA_FIELDS.
    Prefers Target.extra_fields JSON (from TOM), falling back to model attributes.
    """
    exclude_fields = {
        'name',
        'tidesclass',
        'tidesclass_other',
        'tidesclass_subclass',
        'auto_tidesclass',
        'auto_tidesclass_other',
        'auto_tidesclass_subclass',
        'auto_tidesclass_prob',
        'human_tidesclass',
        'human_tidesclass_other',
        'human_tidesclass_subclass',
    }

    extra_fields_spec = getattr(settings, 'EXTRA_FIELDS', []) or []
    extra_store = getattr(target, 'extra_fields', None) or {}

    extras = {}
    for spec in extra_fields_spec:
        name = spec.get('name')
        if not name or spec.get('hidden', False) or name in exclude_fields:
            continue
        # Prefer JSON value; fall back to attribute/property
        val = extra_store.get(name)
        if val is None:
            val = getattr(target, name, '')
        extras[name] = val

    # add Lasair links
    try:
        ztfname = find_target_name(target.ra, target.dec, "ztf")
        lsstname = find_target_name(target.ra, target.dec, "lsst")
    except Exception as exc:
        print(exc)
        return {'target': target, 'extras': extras}
    if ztfname is not None:
        ztflink = "https://lasair-ztf.lsst.ac.uk/objects/" + ztfname
    else:
        ztflink = ''
    if lsstname is not None:
        lsstlink = "https://lasair-lsst.lsst.ac.uk/objects/" + lsstname
    else:
        lsstlink = ''
    return {'target': target, 'extras': extras, 
            'ztfname': ztfname, 'lsstname': lsstname,
            'ztflink': ztflink, 'lsstlink': lsstlink,
            }

@register.inclusion_tag('custom_code/partials/target_classifications.html')
def target_classifications(target):
    """
    Displays the classifications of a target.
    """
    tides_pk = target.pk  # parent_link => pk == tides_cand.tides_id
    
    auto_classifications = PipelineClassificationGlobal.objects.filter(
        tides_id=tides_pk
    ).order_by('-probability')
    
    # Also query SNID classifications
    snid_classifications = PipelineClassificationSnid.objects.filter(
        tides_id=tides_pk
    ).order_by('-probability')

    human_qs = HumanClassification.objects.filter(
        tides_id=tides_pk
    ).order_by('-created')

    # Aggregate pipeline classifications
    aggregated_pipeline = None
    if auto_classifications.exists():
        top_auto = (
            auto_classifications.values('sn_type')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        if top_auto:
            # Get the highest probability classification of the most common type for representative z/phase
            most_common_type = top_auto['sn_type']
            representative = auto_classifications.filter(sn_type=most_common_type).order_by('-probability').first()
            
            aggregated_pipeline = {
                'most_common_class': top_auto['sn_type'],
                'count': top_auto['count'],
                'total_submissions': auto_classifications.count(),
                'z': representative.z if representative and representative.z else None,
                'phase': representative.phase if representative and representative.phase else None,
                'probability': representative.probability if representative and representative.probability else None,
            }

    # Aggregate human classifications
    aggregated_human = None
    if human_qs.exists():
        top = (
            human_qs.values('sn_type')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        if top:
            aggregated_human = {
                'most_common_class': top['sn_type'],
                'count': top['count'],
                'total_submissions': human_qs.count(),
            }

    return {
        'target': target,
        'auto_classifications': auto_classifications,
        'snid_classifications': snid_classifications,
        'human_classifications': human_qs,
        'aggregated_pipeline_class': aggregated_pipeline,
        'aggregated_human_class': aggregated_human,
    }

@register.inclusion_tag('custom_code/partials/aladin_finderchart.html')
def aladin_finderchart(target):
    """
    Displays Aladin skyview of the given target along with basic finder chart annotations including a compass
    and a scale bar. The resulting image is downloadable. This templatetag only works for sidereal targets.
    """
    return {'target': target}

@register.inclusion_tag('custom_code/partials/run_snid.html', takes_context=True)
def snid_form(context, target=None):
    """Render SNID form with spectrum selector for the given target."""
    spectra = []
    if target is not None:
        try:
            from custom_code.models import TidesSpec
            spectra = (
                TidesSpec.objects
                .filter(tides=target)
                .order_by('obs_date', 'tides_specid')
            )
        except Exception:
            spectra = []
    return {
        'target': target,
        'spectra': spectra,
        'request': context.get('request'),
    }

@register.inclusion_tag('custom_code/partials/run_ngsf.html', takes_context=True)
def ngsf_form(context, target=None):
    """Render NGSF form with spectrum selector for the given target."""
    spectra = []
    if target is not None:
        try:
            from custom_code.models import TidesSpec
            spectra = (
                TidesSpec.objects
                .filter(tides=target)
                .order_by('obs_date', 'tides_specid')
            )
        except Exception:
            spectra = []
    return {
        'target': target,
        'spectra': spectra,
        'request': context.get('request'),
    }

