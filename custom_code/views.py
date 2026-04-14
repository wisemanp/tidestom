from django.views.generic.edit import FormView
from django.views import View
from django.views.generic import TemplateView, ListView   # <-- add this
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from custom_code.models import (
    TidesTarget,
    Tag,
    TargetTag,
    TidesSpec,
    PipelineClassificationGlobal,
    TidesClass,
    HumanClassification,
)
from workspaces.models import UserWorkspace
from .forms import SnidParamsForm, NGSFParamsForm, TidesTargetForm  # Ensure this is imported
from django.conf import settings
from datetime import datetime, timedelta
from django.utils.timezone import now
import requests
import shutil
import os
import json
import logging
from workspaces import utils
from pathlib import Path
from custom_code.services import filter_by_tags, unreleased_queryset
from django.db import DatabaseError
import csv
from tom_targets.views import TargetUpdateView, TargetDeleteView
from .permissions import strict_targets_for_user

# 1. Add this at the very top level of the file to confirm the module loads
print("DEBUG: custom_code/views.py module loaded", flush=True)

logger = logging.getLogger(__name__)

def get_tides_class_choices():
    """
    Get classification choices by instantiating TidesTargetForm.
    This guarantees we get the exact same list as the form uses.
    """
    # Use print with flush=True to bypass logging config and force output to Docker logs
    print("DEBUG: Starting get_tides_class_choices", flush=True)
    try:
        # Instantiate the form to trigger its __init__ logic (which queries the DB)
        form = TidesTargetForm()
        print(f"DEBUG: Form instantiated. Fields: {list(form.fields.keys())}", flush=True)
        
        field = form.fields.get('tidesclass')
        
        if field:
            print("DEBUG: Found 'tidesclass' field.", flush=True)
            if hasattr(field, 'choices'):
                # Extract just the values (first element of tuple), filtering out empty ones
                raw_choices = list(field.choices)
                print(f"DEBUG: Raw choices sample (first 5): {raw_choices[:5]}", flush=True)
                
                choices = [c[0] for c in raw_choices if c[0]]
                if choices:
                    print(f"DEBUG: Returning {len(choices)} choices from form.", flush=True)
                    return choices
                else:
                    print("DEBUG: Choices list was empty after filtering blanks.", flush=True)
            else:
                print("DEBUG: 'tidesclass' field has no 'choices' attribute.", flush=True)
        else:
            print("DEBUG: 'tidesclass' field NOT found in form.", flush=True)

    except Exception as e:
        print(f"DEBUG: Error inspecting TidesTargetForm: {e}", flush=True)

    # Fallback: If form instantiation fails, try the hardcoded list from forms.py
    print("DEBUG: Falling back to USE_CHOICES from forms.py", flush=True)
    try:
        from .forms import USE_CHOICES
        choices = [c[0] for c in USE_CHOICES]
        print(f"DEBUG: Found USE_CHOICES. Count: {len(choices)}", flush=True)
        return choices
    except (ImportError, AttributeError) as e:
        print(f"DEBUG: Could not import USE_CHOICES: {e}", flush=True)
        return []

class SnidFormAjaxView(FormView):
    form_class = SnidParamsForm

    def form_invalid(self, form):
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    def form_valid(self, form):
        spectrum_id = form.cleaned_data.pop('spectrum', None)
        if not spectrum_id:
            return JsonResponse({"success": False, "error": "No spectrum selected"}, status=400)
        # Resolve by tides_specid (preferred); fallback to JSON additional_info
        spec = None
        try:
            spec = TidesSpec.objects.get(tides_specid=int(spectrum_id))
        except Exception:
            try:
                spec = (
                    TidesSpec.objects
                    .filter(additional_info__TIDES_SPECID=int(spectrum_id))
                    .first()
                )
            except Exception:
                spec = None
        if not spec:
            return JsonResponse({"success": False, "error": "Spectrum not found"}, status=404)
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

        target_name = str(spec.tides_id)
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
            return JsonResponse({"success": False, "error": "No spectrum selected"}, status=400)
        # Resolve by tides_specid (preferred); fallback to JSON additional_info
        spec = None
        try:
            spec = TidesSpec.objects.get(tides_specid=int(spectrum_id))
        except Exception:
            try:
                spec = (
                    TidesSpec.objects
                    .filter(additional_info__TIDES_SPECID=int(spectrum_id))
                    .first()
                )
            except Exception:
                spec = None
        if not spec:
            return JsonResponse({"success": False, "error": "Spectrum not found"}, status=404)
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

        target_name = str(spec.tides_id)
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
        
        # Check if tag is clickable
        if not tag.is_clickable:
            return JsonResponse({
                'error': f'Tag "{tag.name}" cannot be manually toggled'
            }, status=403)

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

        # Simple filters
        z_min = self.request.GET.get('z_min')
        z_max = self.request.GET.get('z_max')
        ctype = self.request.GET.get('class')

        if z_min:
            try:
                ctx['z_min'] = float(z_min)
                # Filter on the related pipeline classification 'z'
                qs = qs.filter(pipeline_classifications_global__z__gte=ctx['z_min'])
            except ValueError:
                pass
        if z_max:
            try:
                ctx['z_max'] = float(z_max)
                # Filter on the related pipeline classification 'z'
                qs = qs.filter(pipeline_classifications_global__z__lte=ctx['z_max'])
            except ValueError:
                pass
        if ctype:
            # Filter on the related pipeline classification 'sn_type'
            qs = qs.filter(pipeline_classifications_global__sn_type=ctype)
            ctx['class'] = ctype

        ctx['targets'] = qs.select_related().distinct()[:1000]
        return ctx


class PublicClassificationsDownloadView(View):
    """Download released classifications as CSV or JSON."""
    def get(self, request):
        from .services import released_queryset
        fmt = request.GET.get('format', 'csv').lower()

        # Prefetch classifications to avoid N+1 queries
        qs = released_queryset().prefetch_related('pipeline_classifications_global')

        rows = []
        for t in qs:
            # Grab the first classification (if any) to get z/type
            pc = t.pipeline_classifications_global.first()
            
            rows.append({
                'tides_id': t.tides_id,
                'name': t.name,
                'auto_class': pc.sn_type if pc else '',
                'auto_prob': pc.probability if pc else '',
                'auto_z': pc.z if pc else '',
            })

        if fmt == 'json':
            return HttpResponse(
                json.dumps(rows, default=str),
                content_type='application/json'
            )

        # default: CSV
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="classifications.csv"'
        writer = csv.DictWriter(resp, fieldnames=['tides_id','name','auto_class','auto_prob','auto_z'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return resp


class LatestView(ListView):
    """
    Latest Spectra (TidesSpec), optionally filtered by the Target's tags
    or Pipeline Classifications.
    """
    template_name = 'latest.html'
    paginate_by = 200
    model = TidesSpec
    context_object_name = 'targets'

    def get_queryset(self):
        # 2. Add debug here to confirm the view is processing the request
        print("DEBUG: LatestView.get_queryset called", flush=True)
        
        # 1. Base: Spectra in the last N days
        try:
            days_range = int(self.request.GET.get('days_range', 60))
        except (ValueError, TypeError):
            days_range = 60
        date_threshold = now() - timedelta(days=days_range)
        
        qs = TidesSpec.objects.filter(obs_date__gte=date_threshold).select_related('tides')

        # 2. Tag Filter (on the related Target) - Handle multiple
        tags = self.request.GET.getlist('tag')
        if tags:
            qs = qs.filter(tides__target_tags__tag__name__in=tags)

        # 3. Class Filter (on the related PipelineClassificationGlobal) - Handle multiple
        classes = self.request.GET.getlist('class')
        if classes:
            qs = qs.filter(tides__pipeline_classifications_global__sn_type__in=classes)

        # 4. Redshift Filter (on the related PipelineClassificationGlobal)
        z_min = self.request.GET.get('z_min')
        z_max = self.request.GET.get('z_max')
        if z_min:
            try:
                qs = qs.filter(tides__pipeline_classifications_global__z__gte=float(z_min))
            except ValueError:
                pass
        if z_max:
            try:
                qs = qs.filter(tides__pipeline_classifications_global__z__lte=float(z_max))
            except ValueError:
                pass

        return qs.distinct().order_by('-obs_date')

    def get_context_data(self, **kwargs):
        # 3. Add debug here to confirm context preparation
        print("DEBUG: LatestView.get_context_data called", flush=True)
        
        context = super().get_context_data(**kwargs)
        
        context['default_days_range'] = self.request.GET.get('days_range', 60)
        context['filter_tags'] = self.request.GET.getlist('tag')
        context['filter_classes'] = self.request.GET.getlist('class')
        context['filter_z_min'] = self.request.GET.get('z_min', '')
        context['filter_z_max'] = self.request.GET.get('z_max', '')

        context['all_tags'] = Tag.objects.filter(is_active=True).order_by('name')
        
        # 4. Call the helper and print the result
        choices = get_tides_class_choices()
        print(f"DEBUG: get_tides_class_choices returned {len(choices)} items: {choices}", flush=True)
        context['all_classes'] = choices

        for spec in context['targets']:
            spec.target = spec.tides

        return context


# --- Release Queue Views ---

class ReleaseQueueView(LoginRequiredMixin, TemplateView):
    template_name = 'custom_code/release_queue.html'

    def get_context_data(self, **kwargs):
        from custom_code.services import update_staging_area
        
        ctx = super().get_context_data(**kwargs)
        
        # Auto-update staging area
        update_staging_area()
        
        # Start with unreleased targets (these are "staged")
        qs = unreleased_queryset().select_related()

        # Filters
        min_prob = self.request.GET.get('min_prob')
        include = self.request.GET.getlist('include_tag')
        exclude = self.request.GET.getlist('exclude_tag')

        if min_prob:
            try:
                qs = qs.filter(pipeline_classifications_global__probability__gte=float(min_prob))
                ctx['min_prob'] = float(min_prob)
            except ValueError:
                pass

        if include:
            qs = filter_by_tags(qs, include_tags=include)
        if exclude:
            qs = filter_by_tags(qs, exclude_tags=exclude)

        # Build enriched target data with classifications and tags
        QUEUE_LIMIT = 500
        qs_distinct = qs.distinct()
        total_unreleased = qs_distinct.count()
        target_data = []
        for target in qs_distinct[:QUEUE_LIMIT]:
            is_ready = target.sync_review_tag()

            auto_class = target.latest_auto_classification
            human_class = target.latest_human_classification

            # Get all tags for this target AFTER syncing them
            target_tags = list(
                target.target_tags
                .select_related('tag')
                .values_list('tag__name', flat=True)
            )
            
            target_data.append({
                'target': target,
                'auto_class': auto_class.sn_type if auto_class else None,
                'auto_subclass': auto_class.notes if auto_class else None,
                'auto_z': auto_class.z if auto_class else None,
                'auto_prob': auto_class.probability if auto_class else None,
                'human_class': human_class.sn_type if human_class else None,
                'human_subclass': human_class.sn_subtype if human_class else None,
                'human_z': human_class.sn_z if human_class else None,
                'tags': target_tags,
                'is_ready': is_ready,
            })
        
        # Sort by ready status first (needs review first), then by name
        target_data.sort(key=lambda x: (x['is_ready'], x['target'].name))
        
        ctx['target_data'] = target_data
        ctx['total_count'] = len(target_data)
        ctx['total_unreleased'] = total_unreleased
        ctx['has_more'] = total_unreleased > QUEUE_LIMIT
        ctx['queue_limit'] = QUEUE_LIMIT
        
        # Context for filter form
        ctx['all_tags'] = Tag.objects.filter(is_active=True).order_by('name')
        ctx['include_tags'] = include
        ctx['exclude_tags'] = exclude
        
        return ctx


class ReleaseQueueActionView(LoginRequiredMixin, View):
    def post(self, request):
        from custom_code.services import get_ready_tag, get_needs_review_tag
        from django.shortcuts import redirect
        from django.urls import reverse

        action = request.POST.get('action')
        ids = request.POST.getlist('target_id')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('release_queue')

        if not ids:
            return redirect(next_url)

        targets = TidesTarget.objects.filter(pk__in=ids)
        ready_tag = get_ready_tag()
        needs_review_tag = get_needs_review_tag()

        if action == 'mark_ready':
            for target in targets:
                TargetTag.objects.get_or_create(tides=target, tag=ready_tag)
                TargetTag.objects.filter(tides=target, tag=needs_review_tag).delete()

        elif action == 'mark_not_ready':
            for target in targets:
                TargetTag.objects.filter(tides=target, tag=ready_tag).delete()
                TargetTag.objects.get_or_create(tides=target, tag=needs_review_tag)

        return redirect(next_url)

class StrictTargetUpdateView(TargetUpdateView):
    """
    Target update view with strict object-level permissions.
    """

    def get_queryset(self, *args, **kwargs):
        qs = super(TargetUpdateView, self).get_queryset(*args, **kwargs)
        return strict_targets_for_user(
            self.request.user,
            qs,
            'change_target'
        )

class StrictTargetDeleteView(TargetDeleteView):

    def get_queryset(self, *args, **kwargs):
        qs = super(TargetDeleteView, self).get_queryset(*args, **kwargs)
        return strict_targets_for_user(
                self.request.user,
                qs,
                'delete_target'
        )
