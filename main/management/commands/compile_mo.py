import os, re, struct, sys
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

MAGIC = 0x950412DE


def unescape(s):
    """Decode .po escape sequences like \\n, \\\", \\\\ (preserving UTF-8)."""
    r = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i + 1]
            if c == "n":
                r.append("\n"); i += 2
            elif c == "t":
                r.append("\t"); i += 2
            elif c == "r":
                r.append("\r"); i += 2
            elif c == '"':
                r.append('"'); i += 2
            elif c == "\\":
                r.append("\\"); i += 2
            else:
                r.append(s[i]); i += 1
        else:
            r.append(s[i]); i += 1
    return "".join(r)


def parse_po(filepath):
    text = Path(filepath).read_text(encoding="utf-8")
    entries = {}
    msgid_val = None
    buf_id = []
    buf_str = []
    in_id = False
    in_str = False

    def flush():
        nonlocal msgid_val
        if msgid_val is not None:
            entries[msgid_val] = "".join(buf_str)
            msgid_val = None

    for line in text.splitlines():
        if line.startswith("msgid "):
            flush()
            val = line[6:].strip()
            buf_id = [unescape(val[1:-1])] if val.startswith('"') and val.endswith('"') else []
            in_id = True
            in_str = False
        elif line.startswith("msgstr "):
            if in_id and buf_id:
                msgid_val = "".join(buf_id)
            val = line[7:].strip()
            buf_str = [unescape(val[1:-1])] if val.startswith('"') and val.endswith('"') else []
            in_id = False
            in_str = True
        elif in_id and line.strip().startswith('"'):
            buf_id.append(unescape(line.strip()[1:-1]))
        elif in_str and line.strip().startswith('"'):
            buf_str.append(unescape(line.strip()[1:-1]))
        elif line.startswith("#,") and "fuzzy" in line:
            in_id = False
            in_str = False
        else:
            in_str = False

    flush()
    return entries


def write_mo(entries, filepath):
    keys = list(entries.keys())
    vals = [entries[k] for k in keys]
    N = len(keys)

    key_bytes = [k.encode("utf-8") for k in keys]
    val_bytes = [v.encode("utf-8") for v in vals]

    # .mo format: header (5x uint32), then orig/trans tables, then string data
    # Length fields do NOT include NUL terminator; offsets advance with NUL.
    header_size = 20
    table_size = 8 * N
    orig_table_off = header_size
    trans_table_off = orig_table_off + table_size
    str_data_off = trans_table_off + table_size

    header = struct.pack("<5I", MAGIC, 0, N, orig_table_off, trans_table_off)

    orig_table = b""
    trans_table = b""
    cur = str_data_off

    for kb in key_bytes:
        orig_table += struct.pack("<2I", len(kb), cur)
        cur += len(kb) + 1

    for vb in val_bytes:
        trans_table += struct.pack("<2I", len(vb), cur)
        cur += len(vb) + 1

    data = header + orig_table + trans_table
    for kb in key_bytes:
        data += kb + b"\0"
    for vb in val_bytes:
        data += vb + b"\0"

    Path(filepath).write_bytes(data)


class Command(BaseCommand):
    help = "Compiles .po to .mo files without gettext"

    def add_arguments(self, parser):
        parser.add_argument(
            "--locale", "-l", dest="locale", help="Locale to process (e.g. de)"
        )

    def handle(self, *args, **options):
        locale_dir = Path(settings.LOCALE_PATHS[0] if settings.LOCALE_PATHS else settings.BASE_DIR / "locale")
        locale_filter = options.get("locale")

        if not locale_dir.exists():
            self.stderr.write(f"Locale directory not found: {locale_dir}")
            return

        for lang_dir in locale_dir.iterdir():
            if not lang_dir.is_dir():
                continue
            lang = lang_dir.name
            if locale_filter and lang != locale_filter:
                continue
            po_file = lang_dir / "LC_MESSAGES" / "django.po"
            mo_file = lang_dir / "LC_MESSAGES" / "django.mo"
            if not po_file.exists():
                continue
            self.stdout.write(f"Compiling {lang}... ", ending="")
            try:
                entries = parse_po(po_file)
                if not entries:
                    self.stdout.write(self.style.WARNING("no entries found"))
                    continue
                write_mo(entries, mo_file)
                self.stdout.write(self.style.SUCCESS(f"OK ({len(entries)} strings)"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"FAILED: {e}"))
