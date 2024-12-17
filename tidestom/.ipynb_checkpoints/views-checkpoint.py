from django.views.generic import TemplateView
from tom_observations.models import BaseTarget as Target


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        return {'targets': Target.objects.all()}