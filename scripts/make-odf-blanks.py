#!/usr/bin/env python3
"""Generate the locale-neutral blank ODF templates in new/default/.

Usage: python3 scripts/make-odf-blanks.py [output-dir]   (default: new/default)

Requires LibreOffice (soffice on PATH) and its Python UNO bridge.

Each file is LibreOffice's own File > New document, saved from a throwaway
profile so no user name, organisation or printer is recorded. The result is
then post-processed so the template is the same for every language:

- the en_GB locale is used only to get A4 paper; all language/country
  defaults are then removed, so editors apply the user's own language
- personal metadata is checked for and reported
- random editing-session ids (rsids) and zip timestamps are removed or fixed, so re-running produces byte-identical files
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import uno
from com.sun.star.beans import PropertyValue

DOCS = [("swriter", "odt", "writer8"), ("scalc", "ods", "calc8"), ("simpress", "odp", "impress8")]

LANG_ATTR = re.compile(r'\s(?:fo:(?:language|country|script)|style:(?:language|country|script)-(?:asian|complex)'
                       r'|style:rfc-language-tag(?:-asian|-complex)?)="[^"]*"')
PERSONAL = re.compile(r'meta:initial-creator|dc:creator|meta:creation-date|dc:date|meta:editing-duration'
                      r'|meta:editing-cycles|meta:user-defined|meta:printed-by'
                      r'|config:name="Printer(?:Name|Setup)"[^/>]*>[^<]|file:///|/home/|C:\\\\', re.I)
# Writer stores random editing-session ids; LibreOffice creates new ones when they are missing
RSID = re.compile(r'<config:config-item config:name="Rsid(?:Root)?" config:type="int">\d+</config:config-item>')


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def generate(out_dir):
    profile = tempfile.mkdtemp(prefix="lo-profile-")
    pipe = "odfblanks%d" % os.getpid()
    env = dict(os.environ, LC_ALL="en_GB.UTF-8", LANG="en_GB.UTF-8")
    proc = subprocess.Popen(["soffice", "-env:UserInstallation=" + uno.systemPathToFileUrl(profile),
                             "--headless", "--invisible", "--norestore", "--accept=pipe,name=%s;urp;" % pipe],
                            env=env)
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        for _ in range(60):
            try:
                ctx = resolver.resolve("uno:pipe,name=%s;urp;StarOffice.ComponentContext" % pipe)
                break
            except Exception:
                time.sleep(0.5)
        else:
            sys.exit("could not connect to soffice")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        paths = []
        for factory, ext, filter_name in DOCS:
            doc = desktop.loadComponentFromURL("private:factory/" + factory, "_blank", 0, (prop("Hidden", True),))
            props = doc.DocumentProperties
            props.Author = props.ModifiedBy = ""
            path = os.path.join(out_dir, "new." + ext)
            doc.storeToURL(uno.systemPathToFileUrl(path), (prop("FilterName", filter_name),))
            doc.close(True)
            paths.append(path)
        try:
            desktop.terminate()
        except Exception:
            pass
        return paths
    finally:
        proc.wait(timeout=30)
        shutil.rmtree(profile, ignore_errors=True)


def sanitize(path):
    with zipfile.ZipFile(path) as z:
        items = [(info.filename, z.read(info.filename)) for info in z.infolist()]
    ok = True
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in items:
            if name.endswith(".xml"):
                text = data.decode("utf-8")
                if name in ("styles.xml", "content.xml"):
                    text = LANG_ATTR.sub("", text)
                elif name == "settings.xml":
                    text = RSID.sub("", text)
                hits = sorted(set(PERSONAL.findall(text)))
                if hits:
                    print("personal data in %s:%s: %s" % (path, name, hits), file=sys.stderr)
                    ok = False
                data = text.encode("utf-8")
            # ODF requires "mimetype" to be the first entry and stored uncompressed
            compress = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            z.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), data, compress_type=compress)
    with open(path, "wb") as f:
        f.write(out.getvalue())
    return ok


def main():
    out_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                              os.path.join(os.path.dirname(__file__), "..", "new", "default"))
    ok = True
    for path in generate(out_dir):
        ok = sanitize(path) and ok
        print("wrote", os.path.relpath(path))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
