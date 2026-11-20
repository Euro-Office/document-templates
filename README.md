## Overview

Template files used to create new documents and documents with sample content in:

- [ONLYOFFICE Documents for Android](https://github.com/ONLYOFFICE/documents-app-android)

## Blank ODF templates

`new/default/` also contains blank `new.odt`, `new.ods` and `new.odp`. They are
locale-neutral (A4, 16:9 slides, no document language), so one copy serves every
language. To regenerate them, install LibreOffice and run:

    python3 scripts/make-odf-blanks.py
