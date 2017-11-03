from aristotle_mdr.tests.settings.settings import *
from aristotle_mdr.required_settings import INSTALLED_APPS

INSTALLED_APPS = (
    'aristotle_pdf',
)+INSTALLED_APPS

ARISTOTLE_SETTINGS['DOWNLOADERS'] = ARISTOTLE_SETTINGS['DOWNLOADERS'] + ["aristotle_pdf.downloader.PDFDownloader"]

ARISTOTLE_SETTINGS['BULK_ACTIONS'] += ['aristotle_pdf.bulk_actions.QuickPDFDownloadForm',]

ROOT_URLCONF = 'aristotle_pdf.tests.urls'
