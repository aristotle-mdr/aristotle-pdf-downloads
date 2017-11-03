from aristotle_mdr.utils import get_download_template_path_for_item
import cgi
import os


from django.http import HttpResponse, Http404
# from django.shortcuts import render
from django.template.loader import select_template, get_template
from django.template import Context
from django.utils.safestring import mark_safe

from aristotle_mdr.contrib.help.models import ConceptHelp

from aristotle_mdr.downloader import DownloaderBase

import logging
import weasyprint

item_register = {
    'pdf': '__template__'
}

PDF_STATIC_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pdf_static')

logger = logging.getLogger(__name__)
logger.debug("Logging started for " + __name__)


class PDFDownloader(DownloaderBase):
    download_type = "pdf"
    metadata_register = '__template__'
    label = "PDF"
    icon_class = "fa-file-pdf-o"
    description = "Downloads for various content types in the PDF format"

    @classmethod
    def download(cls, request, item):
        """Built in download method"""
        template = get_download_template_path_for_item(item, cls.download_type)
        from django.conf import settings
        page_size = getattr(settings, 'PDF_PAGE_SIZE', "A4")

        subItems = [
            (obj_type, qs.visible(request.user).order_by('name').distinct())
            for obj_type, qs in item.get_download_items()
        ]

        return render_to_pdf(
            template,
            {
                'title': "PDF Download for {obj.name}".format(obj=item),
                'item': item,
                'subitems': subItems,
                'tableOfContents': len(subItems) > 0,
                'view': request.GET.get('view', '').lower(),
                'pagesize': request.GET.get('pagesize', page_size),
                'request': request,
            },
        )

    @classmethod
    def bulk_download(cls, request, items, title=None, subtitle=None):
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
            preamble_template='aristotle_mdr/downloads/pdf/bulk_download_title.html',
            debug_as_html=debug_as_html
        )


def generate_outline_str(bookmarks, indent=0):
    outline_str = ""
    for i, (label, (page, _, _), children) in enumerate(bookmarks, 1):
        outline_str += ('<div>%s %d. %s ..... <span style="float:right"> %d </span> </div>' % (
            '&nbsp;' * indent * 2, i, label.lstrip('0123456789. '), page + 1))
        outline_str += generate_outline_str(children, indent + 1)
    return outline_str


def generate_outline_tree(bookmarks, depth=1):
    outline_str = []
    return [
        {'label': label, "depth": depth, "page": page + 1, "children": generate_outline_tree(children, depth + 1)}
        for i, (label, (page, _, _), children) in enumerate(bookmarks, 1)
    ]


def render_to_pdf(template_src, context_dict, preamble_template='aristotle_mdr/downloads/pdf/title.html', debug_as_html=False):
    # If the request template doesnt exist, we will give a default one.
    template = select_template([
        template_src,
        'aristotle_mdr/downloads/pdf/managedContent.html'
    ])

    context = Context(context_dict)
    html = template.render(context)

    if debug_as_html:
        return HttpResponse(html)

    document = weasyprint.HTML(
        string=template.render(context),
        base_url=PDF_STATIC_PATH
    ).render()

    if not context_dict.get('tableOfContents', False):
        return HttpResponse(document.write_pdf(), content_type='application/pdf')

    table_of_contents_string = generate_outline_str(document.make_bookmark_tree())
    toc = get_template('aristotle_mdr/downloads/pdf/toc.html').render(
        Context({
            "toc_tree": generate_outline_tree(document.make_bookmark_tree())
        })
    )

    table_of_contents_document = weasyprint.HTML(
        string=toc,
        base_url=PDF_STATIC_PATH
    ).render()

    if preamble_template:
        title_page = weasyprint.HTML(
            string=get_template(preamble_template).render(context),
            base_url=PDF_STATIC_PATH
        ).render().pages[0]
        document.pages.insert(0, title_page)

    for i, table_of_contents_page in enumerate(table_of_contents_document.pages):
        document.pages.insert(i + 1, table_of_contents_page)

    return HttpResponse(document.write_pdf(), content_type='application/pdf')


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
