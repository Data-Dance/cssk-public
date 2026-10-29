=================
CZ/SK User Guides
=================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

*Accounting → Configuration → Guides* opens ``/cssk/guide``: the start page
of the Czech and Slovak localization's user guide, then the guide of every
module on the server, by topic.

The start page and the topic titles are generated from ``guide/`` in the
source repository by ``tools/gen_module_docs.py`` into ``data/``; edit them
there. The modules are found at run time: every generated guide page carries
``<meta name="cssk-guide-topic">`` and the page lists those present on the
addons path, so a server with several delivery repositories gets one guide.

User documentation: ``static/description/index.html`` (also in Czech and
Slovak).

Credits
=======

* Data Dance s.r.o. — https://www.datadance.eu
