from django.views.generic.edit import FormView
from django.views import View
from django.views.generic import TemplateView, ListView   # <-- add this
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import TidesTarget, Tag, TargetTag, TidesSpec, PipelineClassificationGlobal
from .forms import SnidParamsForm, NGSFParamsForm
from django.conf import settings
from datetime import datetime
import requests
import shutil
import os
import json
import logging
from workspaces import utils
from pathlib import Path
from custom_code.services import filter_by_tags, unreleased_queryset, mark_released, unmark_released

logger = logging.getLogger(__name__)

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

        temp_file_path = '/snid_api_runs/target.fits'
        shutil.copy2(str(p), temp_file_path)
        form.cleaned_data["spectrum"] = temp_file_path

        workspace_obj, workspace_path = UserWorkspace.get_or_create_for_user(
                self.request.user,
                api_name='snid_api',
                )
        if not self.request.user.has_perm('workspaces.view_userworkspace',
                                          workspace_obj):
            logger.warning(f"Permission denied for user {self.request.user.id} on \
                    workspace {workspace_obj.id}")
            return HttpResponseForbidden("You do not have permission to access this\
                    workspace.")

        target_name = str(spectrum_id)
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

        run_dir = Path(workspace_path) / target_name / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        os.chown(run_dir, 1000, 1000)

        form.cleaned_data['output_dir'] = str(run_dir)

        try:
            response = requests.post(
                f"{settings.SNID_API_URL}/snid_params/",
                json=form.cleaned_data,
                timeout=10
            )

            response.raise_for_status()

            metadata_path = run_dir / "metadata.json"
            metadata = {
                    "user": self.request.user.username,
                    "target": target_name,
                    "timestamp": timestamp,
                    "params": form.cleaned_data,
                }
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)


        except requests.exceptions.HTTPError as e:
            return JsonResponse({"success": False, "error": f"HTTP error: {e}"},
                                status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_file_path}: {e}")

        return JsonResponse({"success": True, "data": response.json()})

class PreviousSNIDRunsView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not Authenticated"}, status=403)

        target_id = request.GET.get("target_id")
        if not target_id:
            return JsonResponse({"error": "target_id missing"}, status=400)

        try:
            workspace_obj, workspace_path = UserWorkspace.get_or_create_for_user(
                    request.user, api_name='snid_api'
                    )

            results = utils.list_existing_results(workspace_path, target_id)
            return JsonResponse({"results": results, "count": len(results)}, safe=False)
        except Exception as e:
            logger.exception(f"Failed to list previous SNID Runs for target \
                    {target_id}: {e}")
            JsonResponse({"error": str(e)}, status=500)

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

        temp_file_path = '/ngsf_api_runs/target.fits'
        shutil.copy2(str(p), temp_file_path)
        form.cleaned_data['spectrum'] = temp_file_path

        workspace_obj, workspace_path = UserWorkspace.get_or_create_for_user(
                self.request.user,
                api_name='ngsf_api',
                )
        if not self.request.user.has_perm('workspaces.view_userworkspace',
                                          workspace_obj):
            logger.warning(f"Permission denied for user {self.request.user.id} on \
                    workspace {workspace_obj.id}")
            return HttpResponseForbidden("You do not have permission to access this\
                    workspace.")

        target_name = str(spectrum_id)
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

        run_dir = Path(workspace_path) / target_name / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        os.chown(run_dir, 1000, 1000)

        form.cleaned_data['output_dir'] = str(run_dir)

        try:
            response = requests.post(
                    f"{settings.NGSF_API_URL}/ngsf_params/",
                    json=form.cleaned_data,
                    timeout=100
                )

            response.raise_for_status()
            #os.remove('/ngsf_api_runs/target.fits')

            #return JsonResponse({"success": True, "data": response.json()})
        except Exception as e:
            return JsonResponse({"sucess": False, "errors": str(e)}, status=500)
        finally:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_file_path}: {e}")

        return JsonResponse({"success": True, "data": response.json()})

class ToggleTagView(LoginRequiredMixin, View):
    """
    POST to add/remove a tag for a target. Returns JSON:
    { "toggled": "added" | "removed", "tag": "<tag name>" }
    """
    def post(self, request, target_id, tag_id):
        target = get_object_or_404(TidesTarget, pk=target_id)
        tag = get_object_or_404(Tag, pk=tag_id, is_active=True)

        # TargetTag.tides is a FK to tom_targets.BaseTarget, so pass target (subclass)
        tt, created = TargetTag.objects.get_or_create(
            tides=target,
            tag=tag,
            defaults={'user': request.user},
        )

        if created:
            logger.info("Tag '%s' added to target %s by %s", tag.name, target.id, request.user)
            return JsonResponse({'toggled': 'added', 'tag': tag.name})

        # Already existed: delete to "un-tag"
        tt.delete()
        logger.info("Tag '%s' removed from target %s by %s", tag.name, target.id, request.user)
        return JsonResponse({'toggled': 'removed', 'tag': tag.name})

class TagSearchView(View):
    def get(self, request):
        # Filter targets by exact tag or list tags by substring
        tag_name = request.GET.get('tag')
        q = request.GET.get('q')

        if tag_name:
            targets = (TidesTarget.objects
                       .filter(tags__name=tag_name)
                       .distinct()
                       .values('id', 'name'))
            return JsonResponse({'results': list(targets)})

        if q:
            tags = Tag.objects.filter(name__icontains=q, is_active=True).values('id', 'name')
            return JsonResponse({'results': list(tags)})

        return JsonResponse({'results': []})

class PublicClassificationsView(TemplateView):
    """Public, no-login list of released classifications."""
    template_name = 'custom_code/public_classifications.html'

    def get_context_data(self, **kwargs):
        from .services import released_queryset
        ctx = super().get_context_data(**kwargs)
        qs = released_queryset()

        # Simple filters for now
        z_min = self.request.GET.get('z_min')
        z_max = self.request.GET.get('z_max')
        ctype = self.request.GET.get('class')

        if z_min:
            try:
                ctx['z_min'] = float(z_min)
                qs = qs.filter(auto_tidesclass_z__gte=ctx['z_min'])
            except ValueError:
                pass
        if z_max:
            try:
                ctx['z_max'] = float(z_max)
                qs = qs.filter(auto_tidesclass_z__lte=ctx['z_max'])
            except ValueError:
                pass
        if ctype:
            qs = qs.filter(auto_tidesclass=ctype)
            ctx['class'] = ctype

        ctx['targets'] = qs.select_related()[:1000]  # limit
        return ctx


class PublicClassificationsDownloadView(View):
    """Download released classifications as CSV or JSON."""
    def get(self, request):
        from .services import released_queryset
        fmt = request.GET.get('format', 'csv').lower()

        qs = released_queryset().select_related()

        rows = []
        for t in qs:
            rows.append({
                'tides_id': t.tides_id,
                'name': t.name,
                'auto_class': getattr(t, 'auto_tidesclass', ''),
                'auto_subclass': getattr(t, 'auto_tidesclass_subclass', None).sub_class
                                  if getattr(t, 'auto_tidesclass_subclass', None) else '',
                'auto_prob': getattr(t, 'auto_tidesclass_prob', None),
                'auto_z': getattr(t, 'auto_tidesclass_z', None),
            })

        if fmt == 'json':
            return HttpResponse(
                json.dumps(rows, default=str),
                content_type='application/json'
            )

        # default: CSV
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="classifications.csv"'
        writer = csv.DictWriter(resp, fieldnames=rows[0].keys() if rows else
                                ['tides_id','name','auto_class','auto_subclass','auto_prob','auto_z'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return resp

class LatestView(ListView):
    """
    Latest *classifications*, not just targets.
    Driven by PipelineClassificationGlobal and joined to TidesTarget.
    """
    model = PipelineClassificationGlobal
    template_name = 'latest.html'
    context_object_name = 'classifications'
    paginate_by = 50

    def get_queryset(self):
        qs = (
            PipelineClassificationGlobal.objects
            .select_related('tides_target')              # adjust if FK name differs
            .order_by('-created')                        # or your timestamp field on PCG
        )

        # --- tag filter (on the underlying TidesTarget) ---
        tag = self.request.GET.get('tag')
        if tag:
            target_qs = TidesTarget.objects.all()
            target_qs = filter_by_tags(target_qs, include_tags=[tag])
            qs = qs.filter(tides_target__in=target_qs)

        # --- class filter (dropdown) ---
        ctype = self.request.GET.get('class')
        if ctype:
            qs = qs.filter(sn_type=ctype)  # or use the correct field for your auto class

        # --- redshift filters ---
        z_min = self.request.GET.get('z_min')
        z_max = self.request.GET.get('z_max')
        if z_min:
            try:
                zmin_f = float(z_min)
                qs = qs.filter(sn_z__gte=zmin_f)  # or host_z if that's what you want
            except ValueError:
                pass
        if z_max:
            try:
                zmax_f = float(z_max)
                qs = qs.filter(sn_z__lte=zmax_f)
            except ValueError:
                pass

        # optional: days_range based on created timestamp
        days_range = self.request.GET.get('days_range')
        if days_range:
            try:
                from django.utils.timezone import now
                from datetime import timedelta
                dr = int(days_range)
                qs = qs.filter(created__gte=now() - timedelta(days=dr))
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Make the underlying targets easily available in the template
        pcs = ctx['classifications']
        target_ids = [pc.tides_target_id for pc in pcs if pc.tides_target_id]
        target_map = {
            t.id: t for t in TidesTarget.objects.filter(id__in=target_ids)
        }
        for pc in pcs:
            pc.target = target_map.get(pc.tides_target_id)

        # Filters state
        ctx['default_days_range'] = self.request.GET.get('days_range', '')
        ctx['filter_tag'] = self.request.GET.get('tag', '')
        ctx['filter_class'] = self.request.GET.get('class', '')
        ctx['filter_z_min'] = self.request.GET.get('z_min', '')
        ctx['filter_z_max'] = self.request.GET.get('z_max', '')

        # Tag choices
        ctx['all_tags'] = Tag.objects.filter(is_active=True).order_by('name')

        # Class choices (dropdown) from PipelineClassificationGlobal.sn_type
        ctx['all_classes'] = (
            PipelineClassificationGlobal.objects
            .exclude(sn_type__isnull=True)
            .exclude(sn_type='')
            .values_list('sn_type', flat=True)
            .distinct()
            .order_by('sn_type')
        )

        return ctx