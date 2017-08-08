from aristotle_mdr.utils import get_download_template_path_for_item
import cgi

try:  # Python 2
    from cStringIO import StringIO as BytesIO
except:  # Python 3
    from io import BytesIO


from django.http import HttpResponse, Http404
# from django.shortcuts import render
from django.template.loader import select_template
from django.template import Context
from django.utils.safestring import mark_safe

import csv
from aristotle_mdr.contrib.help.models import ConceptHelp

import weasyprint

item_register = {
    'pdf': '__template__'
}

def generate_outline_str(bookmarks, indent=0):
    outline_str = ""
    for i, (label, (page, _, _), children) in enumerate(bookmarks, 1):
        outline_str += ('<div>%s %d. %s ..... <span style="float:right"> %d </span> </div>' % (
            '&nbsp;' * indent, i, label.lstrip('0123456789. '), page))
        outline_str += generate_outline_str(children, indent + 2)
    return outline_str


def render_to_pdf(template_src, context_dict, debug_as_html=False):
    # If the request template doesnt exist, we will give a default one.
    template = select_template([
        template_src,
        'aristotle_mdr/downloads/pdf/managedContent.html'
    ])
    context = Context(context_dict)
    html = template.render(context)

    if debug_as_html:
        return HttpResponse(html)

    document = weasyprint.HTML(string=template.render(context)).render()

    table_of_contents_string = generate_outline_str(document.make_bookmark_tree())
    table_of_contents_document = weasyprint.HTML(string=table_of_contents_string).render()
    # table_of_contents_page = table_of_contents_document.pages[0]

    document.pages.insert(1, table_of_contents_page)


    # if not pdf.err:
    return HttpResponse(document.write_pdf(), content_type='application/pdf')
    # return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))


def download(request, download_type, item):
    """Built in download method"""
    template = get_download_template_path_for_item(item, download_type)
    from django.conf import settings
    page_size = getattr(settings, 'PDF_PAGE_SIZE', "A4")
    if download_type == "pdf":
        subItems = [
            (obj_type, qs.visible(request.user).order_by('name').distinct())
            for obj_type, qs in item.get_download_items()
        ]
        return render_to_pdf(
            template,
            {
                'item': item,
                'subitems': subItems,
                'tableOfContents': len(subItems) > 0,
                'view': request.GET.get('view', '').lower(),
                'pagesize': request.GET.get('pagesize', page_size),
                'request': request,
            }
        )


def items_for_bulk_download(items, request):
    iids = {}
    item_querysets = {}  # {PythonClass:{help:ConceptHelp,qs:Queryset}}
    for item in items:
        if item and item.can_view(request.user):
            if item.__class__ not in iids.keys():
                iids[item.__class__] = []
            iids[item.__class__].append(item.pk)

            for metadata_type, qs in item.get_download_items():
                if metadata_type not in item_querysets.keys():
                    item_querysets[metadata_type] = {'help': None, 'qs': qs}
                else:
                    item_querysets[metadata_type]['qs'] |= qs

    for metadata_type, ids_set in iids.items():
        query = metadata_type.objects.filter(pk__in=ids_set)
        if metadata_type not in item_querysets.keys():
            item_querysets[metadata_type] = {'help': None, 'qs': query}
        else:
            item_querysets[metadata_type]['qs'] |= query

    for metadata_type in item_querysets.keys():
        item_querysets[metadata_type]['qs'] = item_querysets[metadata_type]['qs'].distinct().visible(request.user)
        item_querysets[metadata_type]['help'] = ConceptHelp.objects.filter(
            app_label=metadata_type._meta.app_label,
            concept_type=metadata_type._meta.model_name
        ).first()

    return item_querysets


def bulk_download(request, download_type, items, title=None, subtitle=None):
    """Built in download method"""
    template = 'aristotle_mdr/downloads/pdf/bulk_download.html'  # %(download_type)
    from django.conf import settings
    page_size = getattr(settings, 'PDF_PAGE_SIZE', "A4")

    item_querysets = items_for_bulk_download(items, request)

    if title is None:
        if request.GET.get('title', None):
            title = request.GET.get('title')
        else:
            title = "Auto-generated document"

    if subtitle is None:
        if request.GET.get('subtitle', None):
            subtitle = request.GET.get('subtitle')
        else:
            _list = "<li>" + "</li><li>".join([item.name for item in items if item]) + "</li>"
            subtitle = mark_safe("Generated from the following metadata items:<ul>%s<ul>" % _list)

    if download_type == "pdf":
        subItems = []

        debug_as_html = bool(request.GET.get('html', ''))

        return render_to_pdf(
            template,
            {
                'title': title,
                'subtitle': subtitle,
                'items': items,
                'included_items': sorted(
                    [(k, v) for k, v in item_querysets.items()],
                    key=lambda k_v: k_v[0]._meta.model_name
                ),
                'pagesize': request.GET.get('pagesize', page_size),
            },
            debug_as_html=debug_as_html
        )