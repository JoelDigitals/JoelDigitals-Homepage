from .models import AffiliateCode, AffiliatePartner, Wallet


def affiliate_ref_status(request):
    ref = request.GET.get("ref", "") or request.session.get("affiliate_ref", "")
    ctx = {"affiliate_ref_code": "", "affiliate_ref_valid": None, "affiliate_ref_own": False, "wallet_balance": 0.00}

    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(user=request.user).first()
        ctx["wallet_balance"] = wallet.balance if wallet else 0.00

    if not ref:
        return ctx

    exists = AffiliateCode.objects.filter(code__iexact=ref, is_active=True).exists()
    is_own = False
    if exists and request.user.is_authenticated:
        try:
            partner = AffiliatePartner.objects.get(user=request.user)
            is_own = AffiliateCode.objects.filter(partner=partner, code__iexact=ref).exists()
        except AffiliatePartner.DoesNotExist:
            pass

    ctx["affiliate_ref_code"] = ref
    ctx["affiliate_ref_valid"] = exists
    ctx["affiliate_ref_own"] = is_own
    return ctx
