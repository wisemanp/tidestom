from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from tom_targets.models import Target
from tom_targets.admin import TargetAdmin as TomTargetAdmin

admin.site.unregister(Target)

@admin.register(Target)
class TargetAdmin(TomTargetAdmin, GuardedModelAdmin):
    pass
