from pathlib import Path
import os
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY','local-prototype-only-change-before-deployment')
DEBUG=os.environ.get('DEBUG','1')=='1'
ALLOWED_HOSTS=['localhost','127.0.0.1','testserver']
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','hub']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.environ.get('PGDATABASE','qahub'),'USER':os.environ.get('PGUSER','qahub'),'PASSWORD':os.environ.get('PGPASSWORD',''),'HOST':os.environ.get('PGHOST','localhost'),'PORT':os.environ.get('PGPORT','5432')}}
if os.environ.get('QA_SQLITE')=='1': DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'demo.sqlite3'}}
STATIC_URL='/static/'
STATICFILES_DIRS=[BASE_DIR/'static']
MEDIA_ROOT=BASE_DIR/'private_storage'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='/login/'
LOGIN_REDIRECT_URL='/'
LOGOUT_REDIRECT_URL='/login/'
LANGUAGE_CODE='es'
TIME_ZONE='America/Lima'
USE_TZ=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
X_FRAME_OPTIONS='DENY'
