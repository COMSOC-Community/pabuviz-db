from django.contrib import admin

from .models import *


# Register your models here.
admin.site.register(Election)
admin.site.register(Project)
admin.site.register(Rule)
admin.site.register(RuleFamily)
admin.site.register(BallotType)
admin.site.register(ElectionMetadata)
admin.site.register(RuleResult)
admin.site.register(RuleResultMetadata)
admin.site.register(RuleResultDataProperty)
