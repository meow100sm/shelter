from django.contrib import admin
from .models import Animal, Photo, VetRecord, Movement

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1

class VetRecordInline(admin.TabularInline):
    model = VetRecord
    extra = 1

class MovementInline(admin.TabularInline):
    model = Movement
    extra = 1

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'species', 'status', 'intake_date')
    list_filter = ('species', 'status')
    search_fields = ('unique_id',)
    inlines = [PhotoInline, VetRecordInline, MovementInline]

@admin.register(VetRecord)
class VetRecordAdmin(admin.ModelAdmin):
    list_display = ('animal', 'date', 'type', 'vet_name', 'next_due_date')
    list_filter = ('type', 'date')

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('animal', 'date', 'reason', 'from_location', 'to_location')