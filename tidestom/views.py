from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django.utils import timezone
from django.views.generic.edit import FormView
# from django.db import models
# from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
# from django.shortcuts import render
# from django.urls import reverse_lazy
#from guardian.mixins import PermissionListMixin
from tom_targets.models import Target
from tom_dataproducts.models import DataProduct
from datetime import timedelta
from collections import Counter
from custom_code.models import TidesTarget, HumanClassification, PipelineClassificationGlobal, TidesSpec
from custom_code.forms import TidesTargetForm
import psycopg2
from django.conf import settings
from django.db import transaction
from django.views.generic.list import ListView
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)

class LatestView(ListView):
    template_name = 'latest.html'
    paginate_by = 200
    model = TidesSpec
    context_object_name = 'targets'

    def get_queryset(self):
        days_range = int(self.request.GET.get('days_range', 30))
        date_threshold = now() - timedelta(days=days_range)
        return TidesSpec.objects.filter(obs_date__gte=date_threshold).order_by('-obs_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['default_days_range'] = self.request.GET.get('days_range', 30)

        specs = context[self.context_object_name]
        # Collect tides_ids from TidesSpec (Django exposes <fk>_id)
        tides_ids = [s.tides_id for s in specs if getattr(s, 'tides_id', None) is not None]
        target_map = {t.pk: t for t in TidesTarget.objects.filter(pk__in=tides_ids)}

        # Attach the corresponding TidesTarget to each spec as .target
        for s in specs:
            s.target = target_map.get(getattr(s, 'tides_id', None))

        return context


class MyTargetDetailView(DetailView):
    model = TidesTarget
    template_name = 'target_detail.html'
    context_object_name = 'target'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = self.get_object()
        # Use remote-backed HumanClassification (FK: tides or tides_id)
        submissions = HumanClassification.objects.filter(tides_id=target.pk)

        context['form'] = TidesTargetForm()

        # Aggregate the most common classification from sn_type
        if submissions.exists():
            aggregated = (
                submissions.values('sn_type')
                .annotate(count=models.Count('id'))
                .order_by('-count')
                .first()
            )
            context['aggregated_human_class'] = {
                'most_common_class': aggregated['sn_type'],
                'count': aggregated['count'],
                'total_submissions': submissions.count(),
            }
        else:
            context['aggregated_human_class'] = None

        # Individual submissions (ordered by remote 'created' column)
        context['human_classifications'] = submissions.order_by('-created')
        return context


class SubmitClassificationView(FormView):
    form_class = TidesTargetForm

    def form_valid(self, form):
        target = get_object_or_404(TidesTarget, id=self.kwargs['target_id'])

        subclass_obj = form.cleaned_data.get('tidesclass_subclass')
        # Support model instance (with .sub_class) or plain string from AJAX form
        sn_subtype = None
        if subclass_obj:
            sn_subtype = getattr(subclass_obj, 'sub_class', None) or str(subclass_obj)

        submission = HumanClassification.objects.create(
            tides=target,
            user=self.request.user.id,
            sn_type=form.cleaned_data['tidesclass'],
            sn_subtype=sn_subtype,
            comments=form.cleaned_data.get('tidesclass_other') or '',
            created=now()
        )
        return redirect('target_detail', pk=self.kwargs['target_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = get_object_or_404(
            TidesTarget, id=self.kwargs['target_id']
        )
        context['form'] = self.get_form()
        return context
    
from django.http import JsonResponse
from custom_code.classification_list import CLASSIFICATIONS

def get_subclasses(request):
    main_class = request.GET.get('main_class') or ''
    logger.info(f"get_subclasses called with main_class={main_class!r}")
    subclasses = CLASSIFICATIONS.get(main_class, [])

    # Normalize to expected keys: id and sub_class
    out = []
    for s in subclasses:
        if isinstance(s, dict):
            label = s.get('sub_class') or s.get('text') or s.get('name') or str(s)
            ident = s.get('id') or s.get('value') or label
        else:
            label = str(s)
            ident = label
        out.append({'id': ident, 'sub_class': label})
    return JsonResponse(out, safe=False)

