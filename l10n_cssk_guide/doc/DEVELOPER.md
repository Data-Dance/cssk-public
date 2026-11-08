# l10n_cssk_guide: developer notes

Not user documentation: this file is not rendered into a page.

## Generation

The start page and the topic titles are generated from `guide/` in the
source repository by `tools/gen_module_docs.py` into `data/`; edit them
there. The modules are found at run time: every generated guide page carries
`<meta name="cssk-guide-topic">` and the page lists those present on the
addons path, so a server with several delivery repositories gets one guide.
