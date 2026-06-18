from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.html import strip_tags
from .models import BlogPost


from django.utils import timezone

class LatestPostsFeed(Feed):
    title = "Joel Digitals Blog"
    description = "Digitale Lösungen, Softwareentwicklung, IT-Services und mehr"

    def feed_url(self):
        return reverse("blog_rss")

    def link(self):
        return reverse("blog_list")

    def items(self):
        return BlogPost.objects.filter(
            is_published=True,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        ).order_by("-published_at")[:50]

    def item_title(self, item):
        lang = get_language() or "de"
        if lang == "en" and item.title_en:
            return item.title_en
        return item.title_de

    def item_description(self, item):
        lang = get_language() or "de"
        content = item.content_en if (lang == "en" and item.content_en) else item.content_de
        plain = strip_tags(content)
        if len(plain) > 400:
            plain = plain[:397] + "..."
        img = item.get_main_image_url()
        if img:
            plain = f"[Bild: {img}]\n\n{plain}"
        return plain

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_link(self, item):
        return reverse("blog_detail", args=[item.slug])

    def item_categories(self, item):
        return [c.name for c in item.categories.all()]

    def item_author_name(self, item):
        return "Joel Digitals"

    def item_guid(self, item):
        return f"blog-{item.slug}"


class AtomLatestPostsFeed(LatestPostsFeed):
    feed_type = Atom1Feed
    subtitle = LatestPostsFeed.description

    def item_description(self, item):
        lang = get_language() or "de"
        return item.content_en if (lang == "en" and item.content_en) else item.content_de
