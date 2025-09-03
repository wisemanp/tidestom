from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.conf import settings
import requests
from pathlib import Path
from custom_code.models import TidesSpec
from .forms import SnidParamsForm, NGSFParamsForm

class SnidFormAjaxView(FormView):
    form_class = SnidParamsForm

    def form_invalid(self, form):
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    def form_valid(self, form):
        spectrum_id = form.cleaned_data.pop('spectrum', None)
        if not spectrum_id:
            return JsonResponse({"success": False, "error": "No spectrum selected"},
                                status=400)
        spec = (TidesSpec.objects
                .filter(tides=spectrum_id)
                .order_by('-obs_date', '-qmost_id')
                .first()
            )
        if not spec:
            return JsonResponse({"success": False, "error": "No spectrum found"},
                                status=400)
        p = Path(spec.filepath)
        if not p.exists():
            candidate = Path(settings.BASE_DIR) / 'data' / 'spectra' / 'test' / p.name
            if candidate.exists():
                p = candidate

        form.cleaned_data["spectrum"] = str(p)
        try:
            response = requests.post(
                    "http://snid_api:8000/snid_params/",
                    json=form.cleaned_data,
                    timeout=10
                    )
            response.raise_for_status()
            return JsonResponse({"success": True, "data":response.json()})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

class NGSFFormAJAXView(FormView):
    form_class = NGSFParamsForm

    def form_invalid(self, form):
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    def form_valid(self, form):
        try:
            response = requests.post(
                    "http://ngsf_api:8000/ngsf_params/",
                    json=form.cleaned_data,
                    timeout=20
                    )
            response.raise_for_status()
            return JsonResponse({"success": True, "data": response.json()})
        except Exception as e:
            return JsonResponse({"sucess": False, "errors": str(e)}, status=500)

