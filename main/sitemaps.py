from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import BlogPost
from landingpages.models import LandingPage
from shop_ourapps.models import App as ShopApp
from wiki.models import Wiki as WikiArticle


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return [
            'home', 'about', 'services', 'contact',
            'blog_list', 'our_apps', 'shop',
            'download_app_list', 'status_overview',
        ]

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        from django.utils import timezone
        return BlogPost.objects.filter(is_published=True, published_at__lte=timezone.now())

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('blog_detail', args=[obj.slug])


class LandingPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return LandingPage.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('landing_page', args=[obj.slug])


class ShopAppSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ShopApp.objects.filter(is_available_for_purchase=True)

    def location(self, obj):
        return reverse('app_detail', args=[obj.slug])


class WikiSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return WikiArticle.objects.filter(is_published=True)

    def location(self, obj):
        return reverse('wiki:detail', args=[obj.slug])
