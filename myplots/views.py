from django.shortcuts import render, get_object_or_404
from custom_code.models import TidesTarget, TidesSpec

from django.http import HttpResponse
from django.conf import settings

from pathlib import Path
import numpy as np
from astropy.io import fits

# Create your views here.

def target_spectroscopy_partial(request, target_id):
    snid_path = request.GET.get("snid_path")
    snid_index = request.GET.get("snid_index")
    ngsf_path = request.GET.get("ngsf_path")
    target = get_object_or_404(TidesTarget, pk=target_id)

    return render(request, "myplots/target_spectroscopy_partial.html", {
        "target": target,
        "snid_path": snid_path,
        "snid_index": snid_index,
        "ngsf_path": ngsf_path,
        })

def download_spectrum_ascii(request, target_id):
    """
    Download the latest spectrum for this target as a simple ASCII file:
    wavelength[Å]  flux[erg/cm^2/s/Å]
    """
    target = get_object_or_404(TidesTarget, pk=target_id)

    # Pick the same spectrum as target_spectroscopy uses
    spec = (
        TidesSpec.objects
        .filter(tides=target)
        .order_by('-obs_date', '-tides_specid')
        .first()
    )
    if not spec or not spec.filepath:
        return HttpResponse(
            "No spectrum available for this target.",
            content_type="text/plain",
            status=404,
        )

    p = Path(spec.filepath)
    # Same fallback logic as in myplots_tags.target_spectroscopy
    if not p.exists():
        candidate = Path(settings.BASE_DIR) / "data" / "spectra" / "test" / p.name
        if candidate.exists():
            p = candidate

    try:
        if str(p).endswith("fits"):
            data = fits.getdata(str(p))
            wave = data["WAVE"][0]
            flux = data["FLUX"][0]
            error = data.get("ERROR", [None] * len(wave)) if hasattr(data, 'get') else None
        elif str(p).lower().endswith((".txt", ".ascii", ".dat")):
            # Files have format: "# Wavelength Flux Error Quality"
            data = np.loadtxt(str(p))
            wave = data[:, 0]
            flux = data[:, 1]
            error = data[:, 2] if data.shape[1] > 2 else None
        else:
            raise ValueError(f"Unsupported spectrum file format: {p}")
    except Exception as e:
        return HttpResponse(
            f"Failed to load spectrum: {e}",
            content_type="text/plain",
            status=500,
        )

    # Build ASCII content: wavelength flux error
    if error is not None and len(error) == len(wave):
        lines = ["# wavelength  flux  error"]
        for w, f, e in zip(wave, flux, error):
            lines.append(f"{float(w):.6f} {float(f):.6e} {float(e):.6e}")
    else:
        lines = ["# wavelength  flux"]
        for w, f in zip(wave, flux):
            lines.append(f"{float(w):.6f} {float(f):.6e}")
    content = "\n".join(lines)

    # Filename: TARGETNAME_spectrum.txt
    safe_name = str(target).replace(" ", "_")
    filename = f"{safe_name}_spectrum.ascii"

    resp = HttpResponse(content, content_type="text/plain; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

def download_spectrum_by_specid(request, tides_specid):
    """
    Download a specific spectrum by tides_specid as ASCII file:
    wavelength[Å]  flux[erg/cm^2/s/Å]
    """
    spec = get_object_or_404(TidesSpec, tides_specid=tides_specid)
    
    if not spec.filepath:
        return HttpResponse(
            "No spectrum file available for this specid.",
            content_type="text/plain",
            status=404,
        )

    p = Path(spec.filepath)
    # Same fallback logic
    if not p.exists():
        candidate = Path(settings.BASE_DIR) / "data" / "spectra" / "test" / p.name
        if candidate.exists():
            p = candidate

    try:
        if str(p).endswith("fits"):
            data = fits.getdata(str(p))
            wave = data["WAVE"][0]
            flux = data["FLUX"][0]
            error = data.get("ERROR", [None] * len(wave)) if hasattr(data, 'get') else None
        elif str(p).lower().endswith((".txt", ".ascii", ".dat")):
            # Files have format: "# Wavelength Flux Error Quality"
            data = np.loadtxt(str(p))
            wave = data[:, 0]
            flux = data[:, 1]
            error = data[:, 2] if data.shape[1] > 2 else None
        else:
            raise ValueError(f"Unsupported spectrum file format: {p}")
    except Exception as e:
        return HttpResponse(
            f"Failed to load spectrum: {e}",
            content_type="text/plain",
            status=500,
        )

    # Build ASCII content: wavelength flux error
    if error is not None and len(error) == len(wave):
        lines = ["# wavelength  flux  error"]
        for w, f, e in zip(wave, flux, error):
            lines.append(f"{float(w):.6f} {float(f):.6e} {float(e):.6e}")
    else:
        lines = ["# wavelength  flux"]
        for w, f in zip(wave, flux):
            lines.append(f"{float(w):.6f} {float(f):.6e}")
    content = "\n".join(lines)

    # Filename: SPECID_spectrum.ascii
    filename = f"{tides_specid}_spectrum.ascii"

    resp = HttpResponse(content, content_type="text/plain; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
