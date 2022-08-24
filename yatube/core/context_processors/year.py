from django.utils import timezone


def year(request):
    current_year = timezone.now().year
    return {'current_year': current_year}
