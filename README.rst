Aristotle-pdf-downloads
=======================

This is a rewrite of the PDF download generator for the Aristotle Metadata Registry.


To use this, add a PDF declaration to the ``ARISTOTLE_SETTINGS.DOWNLOADERS`` setting in ``settings.py``::

    ARISTOTLE_SETTINGS = {
        "DOWNLOADERS": [
            # (fileType, menu, font-awesome-icon, module)
            ('pdf', 'PDF', 'fa-file-pdf-o', 'aristotle_pdf', 'Downloads for various content types in the PDF format'),
        ]
    }

And include ``aristotle_pdf`` in ``INSTALLED_APPS`` before ``aristotle_mdr``::

    INSTALLED_APPS = (
        'aristotle_pdf',
        'aristotle_mdr',
    )
