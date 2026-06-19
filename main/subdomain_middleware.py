from django.shortcuts import redirect

class SubdomainRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        path = request.path

        redirects = {
            'download.joel-digitals.de': '/de/downloads/paid/',
            'blog.joel-digitals.de': '/de/blog/',
            'shop.joel-digitals.de': '/de/shop/',
        }

        for subdomain, target in redirects.items():
            if host == subdomain and path == '/':
                return redirect(target)

        return self.get_response(request)
