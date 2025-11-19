from django.shortcuts import render, get_object_or_404
from custom_code.models import TidesTarget

## georgios ##
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings

from pathlib import Path
import numpy as np
from astropy.io import fits

from custom_code.models import TidesTarget, TidesSpec
## georgios ##

# Create your views here.

def target_spectroscopy_partial(request, target_id):
    snid_path = request.GET.get("snid_path")
    target = get_object_or_404(TidesTarget, pk=target_id)

    return render(request, "myplots/target_spectroscopy_partial.html", {
        "target": target,
        "snid_path": snid_path,
        })

# ## georgios ##
# def download_spectrum_ascii(request, target_id):
#     """
#     Download the latest spectrum for this target as a simple ASCII file:
#     wavelength[Å]  flux[erg/cm^2/s/Å]
#     """
#     target = get_object_or_404(TidesTarget, pk=target_id)

#     # Pick the same spectrum as target_spectroscopy uses
#     spec = (
#         TidesSpec.objects
#         .filter(tides=target)
#         .order_by('-obs_date', '-qmost_id')
#         .first()
#     )
#     if not spec or not spec.filepath:
#         return HttpResponse(
#             "No spectrum available for this target.",
#             content_type="text/plain",
#             status=404,
#         )

#     p = Path(spec.filepath)
#     # Same fallback logic as in myplots_tags.target_spectroscopy
#     if not p.exists():
#         candidate = Path(settings.BASE_DIR) / "data" / "spectra" / "test" / p.name
#         if candidate.exists():
#             p = candidate

#     try:
#         if str(p).endswith("fits"):
#             data = fits.getdata(str(p))
#             wave = data["WAVE"][0]
#             flux = data["FLUX"][0]
#         elif str(p).endswith("txt"):
#             data = np.loadtxt(str(p))
#             wave = data[:, 0]
#             flux = data[:, 1]
#         else:
#             raise ValueError(f"Unsupported spectrum file format: {p}")
#     except Exception as e:
#         return HttpResponse(
#             f"Failed to load spectrum: {e}",
#             content_type="text/plain",
#             status=500,
#         )

#     # Build ASCII content: two columns, plus a simple header
#     lines = ["# wavelength [A]  flux [erg_cm^-2_s^-1_A^-1]"]
#     for w, f in zip(wave, flux):
#         lines.append(f"{float(w):.6f} {float(f):.6e}")
#     content = "\n".join(lines)

#     # Nice filename: TARGETNAME_spectrum.txt
#     safe_name = str(target).replace(" ", "_")
#     filename = f"{safe_name}_spectrum.txt"

#     resp = HttpResponse(content, content_type="text/plain; charset=utf-8")
#     resp["Content-Disposition"] = f'attachment; filename="{filename}"'
#     return resp
# ## georgios ##
