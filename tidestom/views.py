from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django.utils import timezone
from django.views.generic.edit import FormView
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from guardian.mixins import PermissionListMixin
from tom_targets.models import Target
from tom_dataproducts.models import DataProduct
from datetime import timedelta
from collections import Counter
from custom_code.models import MirroredTidesTarget,  HumanClassification, PipelineClassificationGlobal  
from custom_code.forms import TidesTargetForm
import psycopg2
from django.conf import settings
from django.db import transaction
from django.views.generic.list import ListView
from django.utils.timezone import now
from custom_code.models import TidesSpec
import logging

logger = logging.getLogger(__name__)

class LatestView(ListView):
    template_name = 'latest.html'
    paginate_by = 200
    model = TidesSpec
    context_object_name = 'targets'

    def get_queryset(self):
        # Default range: last 30 days
        days_range = self.request.GET.get('days_range', 30)
        date_threshold = now() - timedelta(days=int(days_range))

        # Query tides_spec for objects observed within the range
        return TidesSpec.objects.filter(obs_date__gte=date_threshold).order_by('-obs_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['default_days_range'] = self.request.GET.get('days_range', 30)

        # Get matching MirroredTidesTarget objects by tides_id
        tides_ids = [spec.tides_id for spec in context['targets']]
        target_map = {
            t.tides_id: t for t in MirroredTidesTarget.objects.filter(tides_id__in=tides_ids)
        }

        # Attach the corresponding MirroredTidesTarget to each TidesSpec
        for spec in context['targets']:
            spec.mirrored_target = target_map.get(spec.tides_id)

        return context

class MyTargetDetailView(DetailView):
    model = MirroredTidesTarget
    template_name = 'target_detail.html'
    context_object_name = 'target'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = self.get_object()
        submissions = HumanTidesClassSubmission.objects.filter(target=target)
        print(f"Submissions retrieved: {submissions}")  # Debug statement
        # Debug each submission
        for submission in submissions:
            print(f"Submission ID: {submission.id}")
            print(f"Target: {submission.target}")
            print(f"SN Type: {getattr(submission, 'sn_type', None)}")
            print(f"SN Subtype: {getattr(submission, 'sn_subtype', None)}")
        context['form'] = TidesTargetForm()

        # Get all human classification submissions for this target
        submissions = HumanTidesClassSubmission.objects.filter(target=target)
        # Aggregate the most common classification from remote column sn_type
        if submissions.exists():
            print(f"Submissions exist, now trying to count ")  # Debug statement
            tidesclass_counts = Counter(sub.sn_type for sub in submissions if getattr(sub, 'sn_type', None) is not None)
            print("counted ", tidesclass_counts)
            most_common_class, count = tidesclass_counts.most_common(1)[0]
            print("counted, here is most common", most_common_class, count)
            context['aggregated_human_class'] = {
                'most_common_class': most_common_class,
                'count': count,
                'total_submissions': submissions.count(),
            }
        else:
            context['aggregated_human_class'] = None

        # Add all individual submissions to the context (remote column is created, not timestamp)
        context['human_classifications'] = submissions.order_by('-created')
        return context

class SubmitClassificationView(FormView):
    form_class = TidesTargetForm

    def form_valid(self, form):
        target = get_object_or_404(TidesTarget, id=self.kwargs['target_id'])

        # Map form fields to remote schema fields
        subclass_obj = form.cleaned_data.get('tidesclass_subclass')
        sn_subtype = getattr(subclass_obj, 'sub_class', None) if subclass_obj else None

        submission = HumanTidesClassSubmission.objects.create(
            target=target,                          # FK mapped to db_column='tides_id'
            person_id=self.request.user.id,         # remote integer column
            sn_type=form.cleaned_data['tidesclass'],# remote sn_type
            sn_subtype=sn_subtype,                  # remote sn_subtype (text)
            comments=form.cleaned_data.get('tidesclass_other') or '',  # map "other" to comments
            created=now()                           # remote created timestamp
        )
        print(f"Submission saved: {submission}")  # Debug statement
        return redirect('target_detail', pk=self.kwargs['target_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = get_object_or_404(TidesTarget, id=self.kwargs['target_id'])
        context['form'] = self.get_form()
        return context
    
from django.http import JsonResponse
from custom_code.classification_list import CLASSIFICATIONS

def get_subclasses(request):
    main_class_name = request.GET.get('main_class')
    subclasses = CLASSIFICATIONS.get(main_class_name, [])
    return JsonResponse(subclasses, safe=False)

