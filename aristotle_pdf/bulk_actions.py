from django.utils.translation import ugettext_lazy as _

from aristotle_mdr.forms.bulk_actions import DownloadActionForm


class QuickPDFDownloadForm(DownloadActionForm):
    classes="fa-file-pdf-o"
    action_text = _('Quick PDF download')
    items_label = "Items that are downloaded"
    download_type= 'pdf'
    title = None
