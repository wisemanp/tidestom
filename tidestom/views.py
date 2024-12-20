#from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django.utils import timezone
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from guardian.mixins import PermissionListMixin
from tom_targets.models import Target
from tom_targets.filters import TargetFilter
   

from custom_code.models import TidesTarget
from custom_code.forms import TidesTargetForm

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
        recent = timezone.now() - timedelta(days=28)
        context['targets'] = Target.objects.filter(created__gte=recent)
        return context
   
class TargetDetailView(DetailView):
    model = TidesTarget
    template_name = 'target_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TidesTargetForm()
        return context

class SubmitClassificationView(FormView):
    
    form_class = TidesTargetForm

    def form_valid(self, form):
        target = get_object_or_404(TidesTarget, id=self.kwargs['target_id'])
        target.tidesclass = form.cleaned_data['tidesclass']
        target.tidesclass_other = form.cleaned_data['tidesclass_other']
        target.tidesclass_subclass = form.cleaned_data['tidesclass_subclass']
        target.save()
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