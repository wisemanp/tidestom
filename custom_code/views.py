from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.conf import settings
import requests
import shutil
import os
from pathlib import Path
from custom_code.models import TidesSpec
from workspaces import UserWorkspace
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

        shutil.copy2(str(p), '/snid_api_runs/target.fits')
        form.cleaned_data["spectrum"] = '/snid_api_runs/target.fits'

        workspace = UserWorkspace.get_or_create_for_user(self.request.user)
        form.cleaned_data['output_dir'] = workspace.path

        try:
            response = requests.post(
                "http://snid_api:8000/snid_params/",
                json=form.cleaned_data,
                timeout=10
            )

            response.raise_for_status()
            os.remove('/snid_api_runs/target.fits')
            return JsonResponse({"success": True, "data": response.json()})

        except requests.exceptions.HTTPError as e:
            return JsonResponse({"success": False, "error": f"HTTP error: {e}"}, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

class NGSFFormAJAXView(FormView):
    form_class = NGSFParamsForm

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

        shutil.copy2(str(p), '/ngsf_api_runs/target.fits')
        form.cleaned_data['spectrum'] = '/ngsf_api_runs/target.fits'

        try:
            response = requests.post(
                    "http://ngsf_api:8000/ngsf_params/",
                    json=form.cleaned_data,
                    timeout=60
                    )
            response.raise_for_status()
            os.remove('/ngsf_api_runs/target.fits')
            return JsonResponse({"success": True, "data": response.json()})
        except Exception as e:
            return JsonResponse({"sucess": False, "errors": str(e)}, status=500)

