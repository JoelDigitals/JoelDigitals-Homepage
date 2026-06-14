from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Fix blog slugs - add column, generate slugs, add unique constraint"

    def handle(self, *args, **options):
        cursor = connection.cursor()

        self.stdout.write("Adding slug column if not exists...")
        cursor.execute("""
            ALTER TABLE blog_blogpost 
            ADD COLUMN IF NOT EXISTS slug VARCHAR(250) DEFAULT '' NOT NULL
        """)

        self.stdout.write("Generating slugs...")
        cursor.execute("SELECT id, title_de FROM blog_blogpost")
        for row in cursor.fetchall():
            post_id, title = row
            slug = slugify(title) or f"post-{post_id}"
            n = 1
            base = slug
            while True:
                cursor.execute(
                    "SELECT id FROM blog_blogpost WHERE slug=%s AND id!=%s",
                    [slug, post_id]
                )
                if not cursor.fetchone():
                    break
                slug = f"{base}-{n}"
                n += 1
            cursor.execute(
                "UPDATE blog_blogpost SET slug=%s WHERE id=%s",
                [slug, post_id]
            )

        connection.commit()

        self.stdout.write("Adding unique constraint...")
        try:
            cursor.execute("ALTER TABLE blog_blogpost ADD CONSTRAINT blog_blogpost_slug_uniq UNIQUE (slug)")
        except Exception as e:
            self.stdout.write(f"Note: {e}")

        connection.commit()
        self.stdout.write(self.style.SUCCESS("Done! Blog slugs fixed."))
