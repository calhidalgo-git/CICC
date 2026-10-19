"""Certificados: verificación pública por código y listado personal."""

from django.shortcuts import get_object_or_404, render

from ..models import Certificate


def certificate(request, code):
    """Página pública e imprimible; cualquiera con el código puede verificar que la constancia es auténtica."""
    item = get_object_or_404(Certificate.objects.select_related('attempt__user', 'attempt__assessment'), code=code)
    attempt = item.attempt
    return render(
        request,
        'certificate.html',
        {
            'certificate': item,
            'attempt': attempt,
            'holder': attempt.user.get_full_name() or attempt.user.username,
            'is_owner': request.user.is_authenticated and request.user.pk == attempt.user_id,
        },
    )
