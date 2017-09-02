from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
import aristotle_mdr.models as models
import aristotle_mdr.perms as perms
import aristotle_mdr.tests.utils as utils

import datetime

from django.test.utils import setup_test_environment
setup_test_environment()

from aristotle_mdr.tests.main.test_bulk_actions import BulkActionsTest

class QuickPDFDownloadTests(BulkActionsTest, TestCase):

    def test_bulk_quick_pdf_download_on_permitted_items(self):
        self.login_editor()

        self.assertEqual(self.editor.profile.favourites.count(), 0)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'quick_pdf_download',
                'items': [self.item1.id, self.item2.id],
            }
        )
        self.assertEqual(response.status_code, 302)

    def test_bulk_quick_pdf_download_on_forbidden_items(self):
        self.login_editor()

        self.assertEqual(self.editor.profile.favourites.count(), 0)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'quick_pdf_download',
                'items': [self.item1.id, self.item4.id],
            },
            follow=True
        )
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)


class BulkDownloadTests(BulkActionsTest, TestCase):
    download_type="pdf"

    def test_bulk_pdf_download_on_permitted_items(self):
        self.login_editor()

        self.assertEqual(self.editor.profile.favourites.count(), 0)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'bulk_download',
                'items': [self.item1.id, self.item2.id],
                "title": "The title",
                "download_type": self.download_type,
                'confirmed': 'confirmed',
            }
        )
        self.assertEqual(response.status_code, 302)

    def test_bulk_pdf_download_on_forbidden_items(self):
        self.login_editor()

        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'bulk_download',
                'items': [self.item1.id, self.item4.id],
                "title": "The title",
                "download_type": self.download_type,
                'confirmed': 'confirmed',
            },
            follow=True
        )
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)


    def test_bulk_pdf_download_on_forbidden_items_by_anonymous_user(self):
        self.logout()

        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'bulk_download',
                'items': [self.item1.id, self.item4.id],
                "title": "The title",
                "download_type": self.download_type,
                'confirmed': 'confirmed',
            },
            follow=True
        )
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'bulk_download',
                'items': [self.item1.id, self.item4.id],
                "title": "The title",
                "download_type": self.download_type,
                'confirmed': 'confirmed',
            },
        )
        self.assertRedirects(
            response,
            reverse(
                'aristotle:bulk_download',
                kwargs={
                    "download_type": self.download_type,
                }
            )+"?title=The%20title"+"&items=%s&items=%s"%(self.item1.id, self.item4.id)
        )

    def test_content_exists_in_bulk_pdf_download_on_permitted_items(self):
        self.login_editor()

        self.item5 = models.DataElementConcept.objects.create(name="DEC1", definition="DEC5 definition", objectClass=self.item2, workgroup=self.wg1)

        response = self.client.get(
            reverse(
                'aristotle:bulk_download',
                kwargs={
                    "download_type": self.download_type,
                }
            ),
            {
                "items": [self.item1.id, self.item5.id],
                "title": "The title",
                "html": True  # Force HTML to debug content
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertContains(response, self.item2.name)  # Will be in as its a component of DEC5
        self.assertContains(response, self.item5.name)

        self.assertContains(response, self.item1.definition)
        self.assertContains(response, self.item2.definition)  # Will be in as its a component of DEC5
        self.assertContains(response, self.item5.definition)

