from aristotle_mdr.tests.settings.settings import *

INSTALLED_APPS = (
    'aristotle_pdf',
)+INSTALLED_APPS

extra = [
    ('pdf', 'PDF', 'fa-file-pdf-o', 'aristotle_pdf'),
]
try:
    ARISTOTLE_SETTINGS['DOWNLOADERS'] = ARISTOTLE_SETTINGS['DOWNLOADERS'] + extra
except:
    ARISTOTLE_DOWNLOADS = ARISTOTLE_DOWNLOADS + extra

ARISTOTLE_SETTINGS['BULK_ACTIONS'].update({
    'quick_pdf_download':'aristotle_mdr.forms.bulk_actions.QuickPDFDownloadForm',
})
