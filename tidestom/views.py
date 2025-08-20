#from django.views.generic import TemplateView
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
from tom_targets.filters import TargetFilter
from tom_dataproducts.models import DataProduct
from datetime import timedelta
from collections import Counter
from custom_code.models import TidesTarget, HumanTidesClassSubmission  
from custom_code.forms import TidesTargetForm

#from tom_common.mixins import Raise403PermissionRequiredMixin
from datetime import timedelta

from django.utils.timezone import now

class LatestView(PermissionListMixin, FilterView):
    template_name = 'latest.html'
    paginate_by = 200
    strict = False
    model = Target
    filterset_class = TargetFilter
    # Set app_name for Django-Guardian Permissions in case of Custom Target Model
    permission_required = f'{Target._meta.app_label}.view_target'
    ordering = ['-created']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recent = timezone.now() - timedelta(days=356)
        # Filter targets that have associated spectra
        context['targets'] = Target.objects.filter(
            created__gte=recent,
            dataproduct__data_product_type='spectroscopy'
        ).distinct()
        return context

class MyTargetDetailView(DetailView):
    model = TidesTarget
    template_name = 'target_detail.html'
    context_object_name = 'target'
    print('MyTargetDetailView called')
    def __init__(self, *args, **kwargs):
        print("MyTargetDetailView initialized")  # Debug statement
        super().__init__(*args, **kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        print("MyTargetDetailView as_view called")  # Debug statement
        return super().as_view(**initkwargs)
    
    def dispatch(self, request, *args, **kwargs):
        print("TMyargetDetailView dispatch called")  # Debug statement
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        print("MyTargetDetailView get context data called")  # Debug statement
        context = super().get_context_data(**kwargs)
        context['view'] = self  # Explicitly set the view in the context
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
from custom_code.models  import TidesClass, TidesClassSubClass

def get_subclasses(request):
    main_class_name = request.GET.get('main_class')
    try:
        main_class = TidesClass.objects.get(name=main_class_name)
        subclasses = TidesClassSubClass.objects.filter(main_class=main_class).values('id', 'sub_class')
        return JsonResponse(list(subclasses), safe=False)
    except TidesClass.DoesNotExist:
        return JsonResponse([], safe=False)

