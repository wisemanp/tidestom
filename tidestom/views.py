#from django.views.generic import TemplateView
#from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django.utils import timezone
from guardian.mixins import PermissionListMixin
from tom_targets.models import Target
from tom_targets.filters import TargetFilter
#from tom_common.mixins import Raise403PermissionRequiredMixin
from datetime import timedelta


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
        last_24_hours = timezone.now() - timedelta(hours=24)
        context['targets'] = Target.objects.filter(created__gte=last_24_hours)
        return context
   
   