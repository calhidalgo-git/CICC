"""Inicio de sesión con límite de intentos fallidos por usuario y dirección."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.cache import cache
from django.urls import reverse_lazy

from .services import log
from .views.common import ctx

MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60


class ThrottledLoginView(LoginView):
    template_name = 'login.html'

    def throttle_key(self):
        username = self.request.POST.get('username', '').strip().lower()
        return f'login-failures:{username}:{self.request.META.get("REMOTE_ADDR", "")}'

    def post(self, request, *args, **kwargs):
        if cache.get(self.throttle_key(), 0) >= MAX_FAILURES:
            form = self.get_form()
            return self.render_to_response(self.get_context_data(form=form, throttled=True), status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        cache.delete(self.throttle_key())
        return super().form_valid(form)

    def form_invalid(self, form):
        key = self.throttle_key()
        cache.add(key, 0, LOCK_SECONDS)
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, LOCK_SECONDS)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_demo_credentials'] = settings.SHOW_DEMO_CREDENTIALS
        context.setdefault('throttled', False)
        return context


class AccountPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Cambio de contraseña dentro del espacio de trabajo."""

    template_name = 'account_password.html'
    success_url = reverse_lazy('password_change')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['title'] = 'Cambiar contraseña'
        return ctx(self.request, 'account', **data)

    def form_valid(self, form):
        response = super().form_valid(form)
        log(self.request.user, 'Cambio de contraseña')
        messages.success(self.request, 'Tu contraseña se actualizó.')
        return response
