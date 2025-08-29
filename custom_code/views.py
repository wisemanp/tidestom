from django.http import JsonResponse
from django.views.generic.edit import FormView
import requests
from .forms import SnidParamsForm

class SnidFormAjaxView(FormView):
    print('cheeese')
    form_class = SnidParamsForm

    def form_invalid(self, form):
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    def form_valid(self, form):
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

