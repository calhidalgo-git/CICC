from django.contrib import admin
from django.contrib.auth import views as auth
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path

from hub import views as v
from hub.auth import AccountPasswordChangeView, ThrottledLoginView

urlpatterns = [
    path('qa/avanzado/', v.qa_advanced, name='qa_advanced'),
    path('qa/avanzado/semana/<int:week>/', v.qa_advanced_week, name='qa_advanced_week'),
    path('qa/fundamentos/', v.qa_fundamentals, name='qa_fundamentals'),
    path('qa/fundamentos/semana/<int:week>/', v.qa_week, name='qa_week'),
    path('admin/', admin.site.urls),
    path('login/', ThrottledLoginView.as_view(), name='login'),
    path('logout/', auth.LogoutView.as_view(), name='logout'),
    path(
        'password/reset/',
        PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.txt',
            subject_template_name='registration/password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'password/reset/enviado/',
        PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'password/reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm',
    ),
    path(
        'password/reset/completo/',
        PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('cuenta/', v.profile, name='profile'),
    path('cuenta/password/', AccountPasswordChangeView.as_view(), name='password_change'),
    path('', v.page, name='home'),
    path('p/<slug:section>/', v.page, name='page'),
    path('resource/<int:pk>/', v.resource, name='resource'),
    path('favorite/<int:pk>/', v.toggle_favorite, name='favorite'),
    path('resource/<int:pk>/upload/', v.upload_version, name='upload_version'),
    path('download/<int:pk>/', v.download, name='download'),
    path('stream/<int:pk>/', v.stream, name='stream'),
    path('certificate/<str:code>/', v.certificate, name='certificate'),
    path('question/new/', v.question_new, name='question_new'),
    path('question/<int:pk>/edit/', v.question_edit, name='question_edit'),
    path('question/<int:pk>/delete/', v.question_delete, name='question_delete'),
    path('curso/<slug:course>/semana/<int:week>/completar/', v.toggle_week, name='toggle_week'),
    path('exam/<int:pk>/start/', v.start, name='start'),
    path('attempt/<int:pk>/', v.exam, name='exam'),
    path('attempt/<int:pk>/save/', v.save, name='save'),
    path('attempt/<int:pk>/finish/', v.finish, name='finish'),
    path('results/<int:pk>/', v.results, name='results'),
    path('import/', v.import_excel, name='import'),
    path('template/', v.excel_template, name='template'),
    path('report.xlsx', v.report, name='report'),
    path('backup/', v.backup, name='backup'),
    path('restore/', v.restore, name='restore'),
    path('audit.csv', v.audit_csv, name='audit_csv'),
    path('lesson/<int:pk>/complete/', v.complete, name='complete'),
]
