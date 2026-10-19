from django.contrib import admin

from .models import (
    Assessment,
    Attempt,
    Audit,
    Certificate,
    CourseWeek,
    Favorite,
    LearningPath,
    Lesson,
    LessonCheck,
    Notification,
    Progress,
    Question,
    Resource,
    ResourceVersion,
    WeekProgress,
)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'area',
        'minutes',
        'pass_score',
        'max_attempts',
        'questions_per_attempt',
        'opens_at',
        'closes_at',
    )
    filter_horizontal = ('groups',)


class LessonCheckInline(admin.StackedInline):
    model = LessonCheck
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'position')
    inlines = [LessonCheckInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'kind', 'assessment', 'topic')
    list_filter = ('assessment', 'kind', 'topic')
    search_fields = ('text',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'area', 'kind', 'published', 'tags')
    list_filter = ('area', 'kind', 'published')
    filter_horizontal = ('related',)
    search_fields = ('title', 'description')


@admin.register(CourseWeek)
class CourseWeekAdmin(admin.ModelAdmin):
    list_display = ('course', 'number', 'title')
    list_filter = ('course',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('code', 'attempt', 'issued')
    readonly_fields = ('code', 'issued')


for model in (ResourceVersion, LearningPath, Notification, Audit, Progress, Attempt, Favorite, WeekProgress):
    admin.site.register(model)

admin.site.site_header = 'CICC — Centro Integral de Conocimiento de Calidad'
admin.site.site_title = 'CICC'
admin.site.index_title = 'Sección de Control de Calidad'
