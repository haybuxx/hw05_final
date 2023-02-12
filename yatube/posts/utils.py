from django.core.paginator import Paginator
from django.http import HttpRequest
from django.db.models import QuerySet


def get_context_page(request: HttpRequest, queryset: QuerySet, pages: int):
    paginator = Paginator(queryset, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
