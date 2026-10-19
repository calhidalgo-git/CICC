"""Vistas de CICC agrupadas por área. Se reexportan aquí para que ``config.urls`` use ``hub.views``."""

from ..navigation import NAV
from .account import profile
from .certificates import certificate
from .exams import exam, finish, results, save, start
from .learn import (
    complete,
    download,
    qa_advanced,
    qa_advanced_week,
    qa_fundamentals,
    qa_week,
    resource,
    stream,
    toggle_favorite,
    toggle_week,
    upload_version,
)
from .pages import page
from .questions import question_delete, question_edit, question_new
from .tools import audit_csv, backup, excel_template, import_excel, report, restore

__all__ = [
    'NAV',
    'audit_csv',
    'backup',
    'certificate',
    'complete',
    'download',
    'exam',
    'excel_template',
    'finish',
    'import_excel',
    'page',
    'qa_advanced',
    'qa_advanced_week',
    'qa_fundamentals',
    'qa_week',
    'question_delete',
    'question_edit',
    'question_new',
    'profile',
    'report',
    'resource',
    'restore',
    'results',
    'save',
    'start',
    'stream',
    'toggle_favorite',
    'toggle_week',
    'upload_version',
]
