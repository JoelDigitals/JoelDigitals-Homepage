from .models import AffiliateCode, AffiliatePartner


def affiliate_ref_status(request):
    ref = request.GET.get("ref", "") or request.session.get("affiliate_ref", "")
    if not ref:
        return {"affiliate_ref_code": "", "affiliate_ref_valid": None, "affiliate_ref_own": False}

    exists = AffiliateCode.objects.filter(code__iexact=ref, is_active=True).exists()
    is_own = False
    if exists and request.user.is_authenticated:
        try:
            partner = AffiliatePartner.objects.get(user=request.user)
            is_own = AffiliateCode.objects.filter(partner=partner, code__iexact=ref).exists()
        except AffiliatePartner.DoesNotExist:
            pass

    return {
        "affiliate_ref_code": ref,
        "affiliate_ref_valid": exists,
        "affiliate_ref_own": is_own,
    }
