class AffiliateRefMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ref = request.GET.get("ref", "")
        if ref:
            request.session['affiliate_ref'] = ref
        response = self.get_response(request)
        return response
