from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from django.utils import timezone
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect
from tom_targets.models import Target
from tom_dataproducts.models import DataProduct
from datetime import timedelta
from collections import Counter
from custom_code.models import (
    TidesTarget,
    HumanClassification,
    PipelineClassificationGlobal,
    TidesSpec,
    TidesClass,
    TidesClassSubClass,
    Tag,
    TargetTag,
)
from custom_code.forms import TidesTargetForm
import psycopg2
from django.conf import settings
from django.db import transaction
from django.views.generic.list import ListView
from django.utils.timezone import now
import logging
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
import csv
import json
from custom_code.services import (
    filter_by_tags,
    unreleased_queryset,   # make sure these exist in services.py
    mark_released,
    unmark_released,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View   # <-- IMPORTANT

logger = logging.getLogger(__name__)

class LatestView(ListView):
    template_name = 'latest.html'
    paginate_by = 200
    model = TidesSpec
    context_object_name = 'targets'

    def get_queryset(self):
        days_range = int(self.request.GET.get('days_range', 30))
        date_threshold = now() - timedelta(days=days_range)

        # Base queryset: recent spectra
        qs = (
            TidesSpec.objects
            .filter(obs_date__gte=date_threshold)
            .order_by('-obs_date')
        )

        # Collect tides_ids and prefetch their TidesTarget objects
        tides_ids = [s.tides_id for s in qs if getattr(s, 'tides_id', None) is not None]
        targets_qs = TidesTarget.objects.filter(pk__in=tides_ids)

        # Apply filters on the TidesTarget side, then restrict specs to those targets

        # --- Tag filter ---
        tag_name = self.request.GET.get('tag')  # ?tag=high-redshift
        if tag_name:
            targets_qs = filter_by_tags(targets_qs, include_tags=[tag_name])

        # --- Classification type filter ---
        ctype = self.request.GET.get('class')  # ?class=SN Ia, etc.
        if ctype:
            targets_qs = targets_qs.filter(auto_tidesclass=ctype)

        # --- Redshift filters ---
        z_min = self.request.GET.get('z_min')
        z_max = self.request.GET.get('z_max')
        if z_min:
            try:
                zmin_f = float(z_min)
                targets_qs = targets_qs.filter(auto_tidesclass_z__gte=zmin_f)
            except ValueError:
                pass
        if z_max:
            try:
                zmax_f = float(z_max)
                targets_qs = targets_qs.filter(auto_tidesclass_z__lte=zmax_f)
            except ValueError:
                pass

        # Restrict TidesSpec to the filtered targets
        filtered_ids = list(targets_qs.values_list('pk', flat=True))
        qs = qs.filter(tides_id__in=filtered_ids)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Keep existing days_range
        context['default_days_range'] = self.request.GET.get('days_range', 30)

        specs = context[self.context_object_name]

        # Attach the corresponding TidesTarget to each spec as .target
        tides_ids = [s.tides_id for s in specs if getattr(s, 'tides_id', None) is not None]
        target_map = {t.pk: t for t in TidesTarget.objects.filter(pk__in=tides_ids)}

        for s in specs:
            s.target = target_map.get(getattr(s, 'tides_id', None))

        # Expose filters back to template
        context['filter_tag'] = self.request.GET.get('tag', '')
        context['filter_class'] = self.request.GET.get('class', '')
        context['filter_z_min'] = self.request.GET.get('z_min', '')
        context['filter_z_max'] = self.request.GET.get('z_max', '')

        # Optional: all tags for a dropdown in latest.html
        context['all_tags'] = Tag.objects.filter(is_active=True).order_by('name')

        return context


class MyTargetDetailView(DetailView):
    model = TidesTarget
    template_name = 'target_detail.html'
    context_object_name = 'target'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = self.get_object()

        # Detect FK field name on HumanClassification: 'tides_id' (your FK) or legacy 'tides'
        hc_fields = {f.name for f in HumanClassification._meta.get_fields()}
        fk_name = 'tides_id' if 'tides_id' in hc_fields else 'tides'

        submissions = HumanClassification.objects.filter(**{fk_name: target})

        context['form'] = TidesTargetForm()

        # Aggregate the most common classification from sn_type
        if submissions.exists():
            aggregated = (
                submissions.values('sn_type')
                .annotate(count=models.Count('id'))
                .order_by('-count')
                .first()
            )
            context['aggregated_human_class'] = {
                'most_common_class': aggregated['sn_type'],
                'count': aggregated['count'],
                'total_submissions': submissions.count(),
            }
        else:
            context['aggregated_human_class'] = None

        # Individual submissions (ordered by remote 'created' column)
        context['human_classifications'] = submissions.order_by('-created')
        context['tags'] = Tag.objects.filter(is_active=True).order_by('name')  # NEW
        return context


@method_decorator(csrf_exempt, name='dispatch')  # temporarily to rule out CSRF
class SubmitClassificationView(FormView):
    form_class = TidesTargetForm
    template_name = 'target_detail.html'

    def get_form(self):
        form = super().get_form()
        # Determine selected main class (string name)
        main_class_name = self.request.POST.get('tidesclass') or self.request.GET.get('tidesclass') or form.initial.get('tidesclass')
        posted_subclass = self.request.POST.get('tidesclass_subclass')
        logger.info(f"[get_form] main_class_name={main_class_name!r} posted_subclass={posted_subclass!r}")

        # For ModelChoiceField, set queryset that matches the selected main class
        try:
            if main_class_name:
                main_class = TidesClass.objects.get(name=main_class_name)
                form.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.filter(main_class=main_class)
            else:
                form.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.none()
        except TidesClass.DoesNotExist:
            logger.warning(f"[get_form] TidesClass with name={main_class_name!r} does not exist; empty queryset.")
            form.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.none()
        except Exception as e:
            logger.exception(f"[get_form] Failed to set queryset for tidesclass_subclass: {e}")
            form.fields['tidesclass_subclass'].queryset = TidesClassSubClass.objects.none()

        return form

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"[dispatch] method={request.method} path={request.path} kwargs={kwargs}")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.info(f"[post] POST keys={list(request.POST.keys())}")
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        logger.warning(f"[form_invalid] errors={form.errors}")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('target_detail', kwargs={'pk': self.kwargs['target_id']})

    def form_valid(self, form):
        target = get_object_or_404(TidesTarget, pk=self.kwargs['target_id'])
        subclass_obj = form.cleaned_data.get('tidesclass_subclass')
        logger.info(f"[form_valid] cleaned tidesclass={form.cleaned_data.get('tidesclass')!r} subclass={subclass_obj!r}")
        # Support model instance (with .sub_class) or plain string from AJAX form
        sn_subtype = None
        if subclass_obj:
            sn_subtype = getattr(subclass_obj, 'sub_class', None) or str(subclass_obj)
        # Log raw POST payload
        try:
            logger.info(f"SubmitClassificationView POST data: {dict(self.request.POST)}")
        except Exception as e:
            logger.warning(f"Failed to log POST data: {e}")

        # Log cleaned_data
        logger.info(f"SubmitClassificationView cleaned_data: {form.cleaned_data}")


        # Detect FK field names dynamically
        hc_fields = {f.name for f in HumanClassification._meta.get_fields()}
        fk_name = 'tides_id' if 'tides_id' in hc_fields else 'tides'
        user_field = 'user' if 'user' in hc_fields else ('person' if 'person' in hc_fields else None)

        create_kwargs = {
            fk_name: target,
            'sn_type': form.cleaned_data['tidesclass'],
            'sn_subtype': sn_subtype,
            'sn_z': form.cleaned_data.get('sn_z'),
            'host_z': form.cleaned_data.get('host_z'),
            'phase': form.cleaned_data.get('phase'),
            'comments': form.cleaned_data.get('tidesclass_other') or '',
            'created': now(),
        }
        if user_field:
            create_kwargs[user_field] = self.request.user

        # Log what we will insert
        safe_kwargs = {**create_kwargs}
        safe_kwargs[fk_name] = getattr(target, 'pk', target)  # avoid logging full model
        if user_field in safe_kwargs:
            safe_kwargs[user_field] = getattr(self.request.user, 'pk', self.request.user)
        logger.info(f"HumanClassification.create kwargs: {safe_kwargs}")

        # Perform insert with detailed error logging
        try:
            before_count = HumanClassification.objects.filter(**{fk_name: target}).count()
            obj = HumanClassification.objects.create(**create_kwargs)
            after_count = HumanClassification.objects.filter(**{fk_name: target}).count()
            logger.info(f"HumanClassification saved id={obj.pk} for target={target.pk} (count {before_count} -> {after_count})")
        except Exception as e:
            logger.exception(f"Failed to save HumanClassification for target={target.pk}: {e}")
            # Optionally, re-raise or add a message; for now redirect to detail with failure logged.
            return redirect(self.get_success_url())

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = get_object_or_404(TidesTarget, pk=self.kwargs['target_id'])
        context['target'] = target
        context['object'] = target
        context['form'] = self.get_form()
        return context

def get_subclasses(request):
    main_class_name = request.GET.get('main_class') or ''
    logger.info(f"get_subclasses called with main_class={main_class_name!r}")
    out = []
    if not main_class_name:
        return JsonResponse(out, safe=False)
    try:
        main_class = TidesClass.objects.get(name=main_class_name)
        qs = TidesClassSubClass.objects.filter(main_class=main_class).order_by('sub_class')
        # Return pk and label so the browser posts the pk expected by ModelChoiceField
        out = [{'id': str(s.pk), 'sub_class': s.sub_class} for s in qs]
    except TidesClass.DoesNotExist:
        logger.warning(f"[get_subclasses] No TidesClass with name={main_class_name!r}")
    except Exception as e:
        logger.exception(f"[get_subclasses] Error fetching subclasses: {e}")
    return JsonResponse(out, safe=False)

class ToggleTagView(LoginRequiredMixin, View):
    def post(self, request, target_id, tag_id):
        target = get_object_or_404(TidesTarget, pk=target_id)
        tag = get_object_or_404(Tag, pk=tag_id, is_active=True)
        tt, created = TargetTag.objects.get_or_create(
            tides=target,
            tag=tag,
            defaults={'user': request.user},
        )
        if created:
            return JsonResponse({'toggled': 'added', 'tag': tag.name})
        tt.delete()
        return JsonResponse({'toggled': 'removed', 'tag': tag.name})


class ReleaseQueueView(LoginRequiredMixin, TemplateView):
    """
    Staging area: show unreleased targets, with filters on auto prob and tags.
    """
    template_name = 'custom_code/release_queue.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # base: unreleased
        qs = unreleased_queryset()

        # filters from query params
        min_prob = self.request.GET.get('min_prob')
        include = self.request.GET.getlist('include_tag')  # ?include_tag=high-redshift&include_tag=...
        exclude = self.request.GET.getlist('exclude_tag')

        if min_prob:
            try:
                mp = float(min_prob)
                qs = qs.filter(auto_tidesclass_prob__gte=mp)
                ctx['min_prob'] = mp
            except ValueError:
                pass

        if include:
            qs = filter_by_tags(qs, include_tags=include)
        if exclude:
            qs = filter_by_tags(qs, exclude_tags=exclude)

        ctx['targets'] = qs.select_related()[:500]  # safety limit
        ctx['all_tags'] = Tag.objects.filter(is_active=True).order_by('name')
        ctx['include_tags'] = include
        ctx['exclude_tags'] = exclude
        return ctx


class ReleaseQueueActionView(LoginRequiredMixin, View):
    """
    POST endpoint to mark/unmark 'released' for a selection of targets from the queue.
    """
    def post(self, request):
        action = request.POST.get('action')  # 'mark' or 'unmark'
        ids = request.POST.getlist('target_id')  # repeated target_id fields
        targets = TidesTarget.objects.filter(pk__in=ids)

        if action == 'mark':
            n = mark_released(targets, request.user)
        elif action == 'unmark':
            n = unmark_released(targets)
        else:
            return JsonResponse({'error': 'Unknown action'}, status=400)

        return JsonResponse({'updated': n})

