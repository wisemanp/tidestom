from django.shortcuts import render, get_object_or_404
from custom_code.models import TidesTarget

# Create your views here.

def target_spectroscopy_partial(request, target_id):
    snid_path = request.GET.get("snid_path")
    ngsf_path = request.GET.get("ngsf_path")
    target = get_object_or_404(TidesTarget, pk=target_id)

    return render(request, "myplots/target_spectroscopy_partial.html", {
        "target": target,
        "snid_path": snid_path,
        "ngsf_path": ngsf_path,
        })
