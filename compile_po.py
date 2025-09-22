# compile_po.py
import polib
import os

locales = ['de', 'en']
base_path = os.path.join(os.path.dirname(__file__), 'locale')

for lang in locales:
    po_path = os.path.join(base_path, lang, 'LC_MESSAGES', 'django.po')
    mo_path = os.path.join(base_path, lang, 'LC_MESSAGES', 'django.mo')
    po = polib.pofile(po_path)
    po.save_as_mofile(mo_path)
    print(f"Compiled {po_path} -> {mo_path}")
