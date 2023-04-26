from django.contrib import admin

from habit.models import Habit, Tracking

admin.site.register(Habit)
admin.site.register(Tracking)
