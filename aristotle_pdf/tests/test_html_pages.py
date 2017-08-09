from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.test.utils import setup_test_environment
from django.utils import timezone

import aristotle_mdr.models as models
import aristotle_mdr.perms as perms
from aristotle_mdr.utils import url_slugify_concept
from aristotle_mdr.forms.creation_wizards import (
    WorkgroupVerificationMixin,
    CheckIfModifiedMixin
)

setup_test_environment()
from aristotle_mdr.tests import utils
import datetime


def setUpModule():
    from django.core.management import call_command
    call_command('load_aristotle_help', verbosity=0, interactive=False)


class LoggedInViewConceptPages(utils.LoggedInViewPages):
    defaults = {}
    def setUp(self):
        super(LoggedInViewConceptPages, self).setUp()

        self.item1 = self.itemType.objects.create(
            name="Test Item 1 (visible to tested viewers)",
            definition="my definition",
            workgroup=self.wg1,
            **self.defaults
        )
        self.item2 = self.itemType.objects.create(
            name="Test Item 2 (NOT visible to tested viewers)",
            definition="my definition",
            workgroup=self.wg2,
            **self.defaults
        )
        self.item3 = self.itemType.objects.create(
            name="Test Item 3 (visible to tested viewers)",
            definition="my definition",
            workgroup=self.wg1,
            **self.defaults
        )

    def test_su_can_download_pdf(self):
        self.login_superuser()
        response = self.client.get(reverse('aristotle:download',args=['pdf',self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:download',args=['pdf',self.item2.id]))
        self.assertEqual(response.status_code,200)

    def test_editor_can_download_pdf(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:download',args=['pdf',self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:download',args=['pdf',self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_viewer_can_download_pdf(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:download',args=['pdf',self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:download',args=['pdf',self.item2.id]))
        self.assertEqual(response.status_code,403)


class ObjectClassViewPage(LoggedInViewConceptPages, TestCase):
    url_name='objectClass'
    itemType=models.ObjectClass
class PropertyViewPage(LoggedInViewConceptPages, TestCase):
    url_name='property'
    itemType=models.Property
class UnitOfMeasureViewPage(LoggedInViewConceptPages, TestCase):
    url_name='unitOfMeasure'
    itemType=models.UnitOfMeasure
class ValueDomainViewPage(LoggedInViewConceptPages, TestCase):
    url_name='valueDomain'
    itemType=models.ValueDomain
    def setUp(self):
        super(ValueDomainViewPage, self).setUp()

        for i in range(4):
            models.PermissibleValue.objects.create(
                value=i,meaning="test permissible meaning %d"%i,order=i,valueDomain=self.item1
                )
        for i in range(4):
            models.SupplementaryValue.objects.create(
                value=i,meaning="test supplementary meaning %d"%i,order=i,valueDomain=self.item1
                )

class ConceptualDomainViewPage(LoggedInViewConceptPages, TestCase):
    url_name='conceptualDomain'
    itemType=models.ConceptualDomain
class DataElementConceptViewPage(LoggedInViewConceptPages, TestCase):
    url_name='dataElementConcept'
    itemType=models.DataElementConcept
    run_cascade_tests = True

    def setUp(self, *args, **kwargs):
        super(DataElementConceptViewPage, self).setUp(*args, **kwargs)
        self.oc = models.ObjectClass.objects.create(
            name="sub item OC",
            workgroup=self.item1.workgroup,
        )
        self.prop = models.Property.objects.create(
            name="sub item prop",
            workgroup=self.item1.workgroup
        )
        self.item1.objectClass = self.oc
        self.item1.property = self.prop
        self.item1.save()
        self.assertTrue(self.oc.can_view(self.editor))
        self.assertTrue(self.prop.can_view(self.editor))


class DataElementViewPage(LoggedInViewConceptPages, TestCase):
    url_name='dataElement'
    itemType=models.DataElement


class DataElementDerivationViewPage(LoggedInViewConceptPages, TestCase):
    url_name='dataelementderivation'
    itemType=models.DataElementDerivation
