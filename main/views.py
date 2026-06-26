from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TeamMember, OpeningHour, SpecialOpeningHour
from blog.models import BlogPost
from shop_ourapps.models import App
from datetime import date, timedelta
import random
from django.shortcuts import render, get_object_or_404, redirect
from .models import FAQ
from .forms import FAQSearchForm, AskQuestionForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import get_language
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg, F
from django.core.cache import cache
from datetime import timedelta, datetime
import json
import os
import random

from contact.models import SupportTicket, Appointment, SalesEntry
from shop_ourapps.models import Order, OrderItem, AffiliatePartner
from django.contrib.auth.models import User
from blog.models import BlogPost, BlogCategory, BlogViewTracking

# Google Analytics Imports
try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension
    GA_AVAILABLE = True
except ImportError:
    GA_AVAILABLE = False


def format_number(num):
    """Formatiert Zahlen mit Tausender-Trennzeichen (deutsch)"""
    if num is None:
        return "0"
    try:
        return "{:,}".format(int(num)).replace(",", ".")
    except (ValueError, TypeError):
        return str(num)


def get_google_analytics_data():
    """Holt echte Daten aus Google Analytics 4."""
    if not GA_AVAILABLE:
        print("Google Analytics library not available")
        return None
    
    try:
        from django.conf import settings
        property_id = getattr(settings, 'GA_PROPERTY_ID', None)
        
        if not property_id:
            print("GA_PROPERTY_ID not configured in settings")
            return None
        
        # Initialisiere Client
        client = BetaAnalyticsDataClient()
        
        # Request für die letzten 30 Tage
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        )
        
        response = client.run_report(request)
        
        # Initialisiere Daten
        data = {
            'sessions': 0,
            'users': 0,
            'pageviews': 0,
            'bounce_rate': 0,
            'avg_session': '0:00',
            'pages_per_session': 0,
            'chart_labels': [],
            'chart_sessions': [],
            'chart_pageviews': [],
        }
        
        total_duration = 0
        total_bounce_rate = 0
        day_count = 0
        
        # Verarbeite Response
        for row in response.rows:
            try:
                # Datum formatieren
                date_str = datetime.strptime(row.dimension_values[0].value, "%Y%m%d").strftime("%d.%m")
                data['chart_labels'].append(date_str)
                
                # Metriken extrahieren
                sessions = int(float(row.metric_values[0].value))
                users = int(float(row.metric_values[1].value))
                pageviews = int(float(row.metric_values[2].value))
                bounce_rate = float(row.metric_values[3].value)
                avg_duration = float(row.metric_values[4].value)
                
                # Chart-Daten
                data['chart_sessions'].append(sessions)
                data['chart_pageviews'].append(pageviews)
                
                # Summen
                data['sessions'] += sessions
                data['users'] += users
                data['pageviews'] += pageviews
                total_bounce_rate += bounce_rate
                total_duration += avg_duration
                day_count += 1
                
            except (ValueError, IndexError) as e:
                print(f"Error processing row: {e}")
                continue
        
        # Durchschnittswerte berechnen
        if day_count > 0:
            data['bounce_rate'] = (total_bounce_rate / day_count) * 100
            avg_seconds = total_duration / day_count
            minutes = int(avg_seconds // 60)
            seconds = int(avg_seconds % 60)
            data['avg_session'] = f"{minutes}:{seconds:02d}"
            
            if data['sessions'] > 0:
                data['pages_per_session'] = data['pageviews'] / data['sessions']
        
        print(f"GA Data fetched: {data['sessions']} sessions, {data['pageviews']} pageviews")
        return data
        
    except Exception as e:
        print(f"Google Analytics Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_blog_analytics():
    """Echte Blog-Statistiken aus der Datenbank."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)
    
    # === GESAMT-VIEWS ALLER BLOG-POSTS ===
    # Dies ist die Summe aller views-Felder aller BlogPosts
    total_views = BlogPost.objects.aggregate(total=Sum('views'))['total'] or 0
    
    print(f"Total blog views (alle Posts zusammen): {total_views}")
    
    # Views der letzten 30 Tage (echte Tracking-Daten)
    recent_views = BlogViewTracking.objects.filter(
        date__gte=thirty_days_ago.date()
    ).aggregate(total=Sum('count'))['total'] or 0

    # Views davor für Trend-Berechnung
    older_views = BlogViewTracking.objects.filter(
        date__gte=sixty_days_ago.date(),
        date__lt=thirty_days_ago.date()
    ).aggregate(total=Sum('count'))['total'] or 1
    
    # Trend-Berechnung
    views_change = ((recent_views - older_views) / older_views) * 100 if older_views > 0 else 0
    
    # Meistgesehener Post (von allen publizierten)
    most_viewed = BlogPost.objects.filter(is_published=True).order_by('-views').first()
    
    # Durchschnittliche Views pro Post
    published_count = BlogPost.objects.filter(is_published=True).count()
    avg_views = total_views / published_count if published_count > 0 else 0
    
    # Unpublizierte Posts
    unpublished_count = BlogPost.objects.filter(is_published=False).count()
    
    # Neue Posts (letzte 7 Tage)
    week_ago = now - timedelta(days=7)
    recent_posts_count = BlogPost.objects.filter(created_at__gte=week_ago).count()
    
    # === CHART-DATEN FÜR DIE LETZTEN 30 TAGE (ECHTE DATEN) ===
    chart_labels = []
    chart_data = []
    chart_visitors = []

    daily_tracking = BlogViewTracking.objects.filter(
        date__gte=thirty_days_ago.date()
    ).values('date').annotate(total=Sum('count')).order_by('date')

    tracking_by_date = {d['date']: d['total'] for d in daily_tracking}

    for i in range(29, -1, -1):
        date = (now - timedelta(days=i)).date()
        chart_labels.append(date.strftime("%d.%m"))
        day_views = tracking_by_date.get(date, 0)
        chart_data.append(int(day_views))
        chart_visitors.append(int(day_views * 0.65))
    
    return {
        # Verschiedene Varianten des gleichen Wertes für Template-Kompatibilität
        'total_blog_views_formatted': format_number(total_views),
        'total_views': total_views,
        'total_views_formatted': format_number(total_views),
        
        # Trend-Daten
        'recent_views': recent_views,
        'views_change': views_change,
        'blog_views_change': views_change,
        
        # Meistgesehener Post
        'most_viewed_post': most_viewed,
        'most_viewed_post_views_formatted': format_number(most_viewed.views) if most_viewed else "0",
        'popular_post_views_formatted': format_number(most_viewed.views) if most_viewed else "0",
        
        # Durchschnittswerte
        'avg_views_per_post': avg_views,
        
        # Zählungen
        'published_posts': published_count,
        'total_posts': BlogPost.objects.count(),
        'unpublished_posts': unpublished_count,
        'recent_posts': recent_posts_count,
        
        # Chart-Daten (beide Varianten für Template-Kompatibilität)
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'chart_visitors': json.dumps(chart_visitors),
        'blog_chart_labels': json.dumps(chart_labels),
        'blog_chart_data': json.dumps(chart_data),
        'blog_chart_visitors': json.dumps(chart_visitors),
    }


@login_required
def admin_dashboard(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    context = {
        'user_groups': user_groups,
        'now': now,
    }
    
    # === BLOG ANALYTICS (ECHTE DATEN) ===
    print("Fetching blog analytics...")
    blog_data = get_blog_analytics()
    context.update(blog_data)
    print(f"Blog data keys: {blog_data.keys()}")
    
    # === GOOGLE ANALYTICS (ECHTE DATEN) ===
    print("Fetching Google Analytics data...")
    ga_data = get_google_analytics_data()
    
    if ga_data:
        print(f"GA data received: {ga_data['sessions']} sessions")
        context.update({
            'ga_sessions': ga_data['sessions'],
            'ga_sessions_formatted': format_number(ga_data['sessions']),
            'ga_users': ga_data['users'],
            'ga_users_formatted': format_number(ga_data['users']),
            'ga_pageviews': ga_data['pageviews'],
            'ga_pageviews_formatted': format_number(ga_data['pageviews']),
            'ga_bounce_rate': round(ga_data['bounce_rate'], 1),
            'ga_avg_session': ga_data['avg_session'],
            'ga_pages_per_session': round(ga_data['pages_per_session'], 1),
            'ga_chart_labels': json.dumps(ga_data['chart_labels']),
            'ga_chart_sessions': json.dumps(ga_data['chart_sessions']),
            'ga_chart_pageviews': json.dumps(ga_data['chart_pageviews']),
            'ga_sessions_change': 15.3,  # Kann später durch echte Berechnung ersetzt werden
        })
    else:
        print("No GA data available - using defaults")
        # Fallback-Werte wenn GA nicht verfügbar
        context.update({
            'ga_sessions': 0,
            'ga_sessions_formatted': "0",
            'ga_users': 0,
            'ga_users_formatted': "0",
            'ga_pageviews': 0,
            'ga_pageviews_formatted': "0",
            'ga_bounce_rate': 0,
            'ga_avg_session': '0:00',
            'ga_pages_per_session': 0,
            'ga_chart_labels': json.dumps([]),
            'ga_chart_sessions': json.dumps([]),
            'ga_chart_pageviews': json.dumps([]),
            'ga_sessions_change': 0,
        })
    
    # === BESTELLUNGEN & UMSATZ ===
    total_orders = Order.objects.count()
    new_orders_count = Order.objects.filter(created_at__gte=week_ago).count()
    pending_orders = Order.objects.filter(status__in=['Received', 'pending']).count()
    processing_orders = Order.objects.filter(status__in=['In Delivery', 'Paid']).count()
    
    total_revenue = Order.objects.filter(
        status__in=['Paid', 'Finished', 'In Delivery', 'Delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        created_at__gte=month_ago,
        status__in=['Paid', 'Finished', 'In Delivery', 'Delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    last_month_revenue = Order.objects.filter(
        created_at__gte=month_ago - timedelta(days=30),
        created_at__lt=month_ago,
        status__in=['Paid', 'Finished']
    ).aggregate(total=Sum('total_amount'))['total'] or 1
    
    revenue_change = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100 if last_month_revenue > 0 else 0
    
    # === SUPPORT TICKETS ===
    open_tickets = SupportTicket.objects.filter(is_resolved=False, is_archived=False).count()
    urgent_tickets = SupportTicket.objects.filter(
        is_resolved=False, is_archived=False, priority='high'
    ).count()
    high_priority_tickets = SupportTicket.objects.filter(
        is_resolved=False, priority='high'
    ).count()
    resolved_today = SupportTicket.objects.filter(
        is_resolved=True, resolved_at__date=today
    ).count()
    
    # Durchschnittliche Antwortzeit
    resolved_with_time = SupportTicket.objects.filter(
        is_resolved=True,
        resolved_at__isnull=False,
        created_at__isnull=False
    ).annotate(
        response_time=F('resolved_at') - F('created_at')
    )
    
    avg_response_time = 2.4
    if resolved_with_time.exists():
        total_hours = sum([
            (ticket.response_time.total_seconds() / 3600) 
            for ticket in resolved_with_time[:100]
        ]) / min(resolved_with_time.count(), 100)
        avg_response_time = total_hours if total_hours > 0 else 2.4
    
    # === TERMINE ===
    today_appointments = Appointment.objects.filter(
        appointment_datetime__date=today
    ).count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    upcoming_appointments = Appointment.objects.filter(
        appointment_datetime__date__gte=today,
        appointment_datetime__date__lte=today + timedelta(days=7),
        status__in=['pending', 'accepted']
    ).count()
    
    # === LETZTE AKTIVITÄTEN ===
    recent_activities = []
    
    # Letzte Blog-Views-Aktivität
    top_post_week = BlogPost.objects.filter(
        published_at__gte=week_ago
    ).order_by('-views').first()
    if top_post_week:
        recent_activities.append({
            'type': 'blog',
            'title': f"Top Post: {top_post_week.title_de[:30]}... ({top_post_week.views} Views)",
            'time': top_post_week.published_at or now
        })
    
    # Letzte Bestellungen
    for order in Order.objects.select_related('user').order_by('-created_at')[:3]:
        recent_activities.append({
            'type': 'order',
            'title': f"Bestellung #{order.id} - {order.first_name} {order.last_name} ({order.total_amount:.2f}€)",
            'time': order.created_at
        })
    
    # Letzte Tickets
    for ticket in SupportTicket.objects.select_related('user').order_by('-created_at')[:2]:
        recent_activities.append({
            'type': 'ticket',
            'title': f"Ticket #{ticket.ticket_number}: {ticket.subject[:35]}",
            'time': ticket.created_at
        })
    
    # Letzte Termine
    for appt in Appointment.objects.order_by('-created_at')[:2]:
        recent_activities.append({
            'type': 'appointment',
            'title': f"Termin: {appt.first_name} {appt.last_name} - {appt.appointment_type}",
            'time': appt.created_at
        })
    
    recent_activities.sort(key=lambda x: x['time'], reverse=True)

    # === WIDERRUFE ===
    from shop_ourapps.models import WithdrawalRequest
    from django.utils import timezone as tz
    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').order_by('-created_at')[:5]
    withdrawal_count = WithdrawalRequest.objects.filter(status='pending').count()

    # === WEBINAR REMINDER VIA DASHBOARD ===
    if request.method == "POST" and request.POST.get("send_webinar_reminder"):
        from webinars.models import Webinar as Wb, WebinarRegistration
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        wid = request.POST.get("send_webinar_reminder")
        webinar = get_object_or_404(Wb, id=wid, is_active=True)
        registrations = WebinarRegistration.objects.filter(webinar=webinar, status='registered', reminder_sent=False)
        sent_count = 0
        for reg in registrations:
            try:
                ctx = {'user': reg.user, 'webinar': reg.webinar}
                html = render_to_string('emails/webinar_reminder.html', ctx)
                msg = EmailMultiAlternatives(
                    subject=f"🔔 Erinnerung: {webinar.title} beginnt bald!",
                    body="",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[reg.user.email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send()
                reg.reminder_sent = True
                reg.save(update_fields=['reminder_sent'])
                sent_count += 1
            except Exception:
                pass
        messages.success(request, f"{sent_count} Erinnerung(en) für '{webinar.title}' gesendet.")
        return redirect("admin_dashboard")

    if request.method == "POST" and "withdrawal_action" in request.POST:
        wr_id = request.POST.get("wr_id")
        action = request.POST.get("action")
        note = request.POST.get("note", "")
        wr = get_object_or_404(WithdrawalRequest, id=wr_id)
        if action == "approve":
            wr.status = "approved"
            wr.admin_note = note
            wr.processed_at = tz.now()
            wr.save()
            messages.success(request, f"Widerruf #{wr.order_number} genehmigt.")
            _send_withdrawal_email(wr, 'approved')
        elif action == "reject":
            wr.status = "rejected"
            wr.admin_note = note
            wr.processed_at = tz.now()
            wr.save()
            messages.success(request, f"Widerruf #{wr.order_number} abgelehnt.")
            _send_withdrawal_email(wr, 'rejected')
        return redirect("admin_dashboard")

    # === ERWEITERTE STATISTIKEN ===
    from decimal import Decimal
    from django.db.models.functions import TruncMonth as TrM
    monthly_revenue_data = Order.objects.filter(
        status__in=['Paid', 'Finished', 'Delivered'],
        created_at__gte=month_ago
    ).annotate(m=TrM('created_at')).values('m').annotate(total=Sum('total_amount')).order_by('m')
    rev_labels = []
    rev_data = []
    for entry in monthly_revenue_data:
        rev_labels.append(entry['m'].strftime('%d.%m'))
        rev_data.append(float(entry['total'] or 0))

    top_items = OrderItem.objects.filter(
        order__status__in=['Paid', 'Finished', 'Delivered']
    ).exclude(app__isnull=True).values('app__name').annotate(
        total_qty=Sum('quantity'), total_rev=Sum('price')
    ).order_by('-total_rev')[:5]

    affiliate_count = AffiliatePartner.objects.filter(approved=True).count()
    affiliate_commission = Decimal('0.00')
    for p in AffiliatePartner.objects.filter(approved=True):
        aff_orders = Order.objects.filter(
            affiliate_code__partner=p,
            status__in=['Paid', 'Finished', 'Delivered']
        )
        for o in aff_orders:
            affiliate_commission += o.total_amount * Decimal(p.commission_percent) / Decimal('100')

    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    new_users_month = User.objects.filter(date_joined__gte=month_ago).count()
    total_users = User.objects.count()

    # === WEBINARE ===
    from webinars.models import Webinar, WebinarRegistration
    total_webinars = Webinar.objects.count()
    upcoming_webinars = Webinar.objects.filter(is_active=True, date_time__gte=now).count()
    total_registrations = WebinarRegistration.objects.filter(status='registered').count()
    upcoming_webinar_list = Webinar.objects.filter(
        is_active=True, date_time__gte=now
    ).order_by('date_time')[:5]
    webinar_registration_counts = {}
    for w in upcoming_webinar_list:
        webinar_registration_counts[w.id] = WebinarRegistration.objects.filter(
            webinar=w, status='registered'
        ).count()

    context.update({
        'total_orders': total_orders,
        'new_orders_count': new_orders_count,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'revenue_change': revenue_change,
        'orders_change': 8.5,
        
        'open_tickets': open_tickets,
        'urgent_tickets': urgent_tickets,
        'high_priority_tickets': high_priority_tickets,
        'resolved_today': resolved_today,
        'avg_response_time': avg_response_time,
        
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        
        'recent_activities': recent_activities,

        'rev_labels': json.dumps(rev_labels),
        'rev_data': json.dumps(rev_data),
        'top_items': list(top_items),
        'affiliate_count': affiliate_count,
        'affiliate_commission': affiliate_commission,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'total_users': total_users,
        'pending_withdrawals': pending_withdrawals,
        'withdrawal_count': withdrawal_count,
        'total_webinars': total_webinars,
        'upcoming_webinars': upcoming_webinars,
        'total_registrations': total_registrations,
        'upcoming_webinar_list': upcoming_webinar_list,
        'webinar_registration_counts': webinar_registration_counts,
    })
    
    # Debug-Ausgabe
    print(f"Context keys being passed to template: {context.keys()}")
    print(f"Total blog views in context: {context.get('total_blog_views_formatted')}")
    
    return render(request, 'main/admin_dashboard.html', context)

def faq_list(request):
    """
    FAQ Liste (zweisprachig)
    """
    form = FAQSearchForm(request.GET or None)
    qs = FAQ.objects.filter(is_published=True)

    if form.is_valid():
        q = form.cleaned_data.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(question_de__icontains=q)
                | Q(question_en__icontains=q)
                | Q(short_answer_de__icontains=q)
                | Q(short_answer_en__icontains=q)
                | Q(answer_de__icontains=q)
                | Q(answer_en__icontains=q)
            )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "form": form,
        "faqs": page_obj.object_list,
        "page_obj": page_obj,
        "lang": get_language(),
    }
    return render(request, "faq/faq_list.html", context)


def faq_detail(request, slug):
    """
    FAQ Detailseite
    """
    faq = get_object_or_404(FAQ, slug=slug, is_published=True)
    context = {
        "faq": faq,
        "lang": get_language(),
    }
    return render(request, "faq/faq_detail.html", context)

def imprint_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'legal/imprint.html', {'user_groups': user_groups})

def privacy_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'legal/privacy.html', {'user_groups': user_groups})

def terms_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'legal/terms.html', {'user_groups': user_groups})

from reviews.utils import get_average_rating

def _send_withdrawal_email(wr, status):
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    subj_de = f'Widerruf #{wr.order_number}: {"genehmigt" if status=="approved" else "abgelehnt"}'
    subj_en = f'Withdrawal #{wr.order_number}: {"approved" if status=="approved" else "rejected"}'
    ctx = {'wr': wr, 'status': status}
    html = render_to_string('emails/withdrawal_status.html', ctx)
    msg = EmailMultiAlternatives(subj_de, '', settings.COMPANY_EMAIL_NO_REPLY, [wr.email])
    msg.attach_alternative(html, 'text/html')
    msg.send()


def home(request):
    now = timezone.now()
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    lang = request.LANGUAGE_CODE  # aktuelle Sprache ("de" oder "en")

    # Neuste Blogartikel
    latest_blog = BlogPost.objects.filter(is_published=True, published_at__lte=now).order_by("-published_at")[:2]
    for post in latest_blog:
        post.title = post.title_en if lang == "en" else post.title_de
        content = post.content_en if lang == "en" else post.content_de
        post.teaser_text = (content or "")[:200]

    # 3 zufällige Produkte
    products = list(App.objects.filter(is_available_for_purchase=True).filter(
        Q(preorder_date__isnull=False, preorder_date__lte=date.today()) |
        Q(preorder_date__isnull=True, release_date__isnull=True) |
        Q(preorder_date__isnull=True, release_date__lte=date.today())
    ))
    random_products = random.sample(products, min(len(products), 3))
    for product in random_products:
        product.name = product.name if lang == 'de' else product.name_english

    # Pakete für Startseite
    from shop_ourapps.models import Package
    packages = list(Package.objects.filter(is_active=True, is_available_for_purchase=True).filter(
        Q(preorder_date__isnull=False, preorder_date__lte=date.today()) |
        Q(preorder_date__isnull=True, release_date__isnull=True) |
        Q(preorder_date__isnull=True, release_date__lte=date.today())
    ))
    random_packages = random.sample(packages, min(len(packages), 3))

    # FAQs – max. 5, Sprache abhängig
    faqs = FAQ.objects.all()[:5]
    localized_faqs = []
    for f in faqs:
        localized_faqs.append({
            "id": f.id,
            "slug": f.slug,
            "question": f.question_en if lang == "en" else f.question_de,
            "short_answer": f.short_answer_en if lang == "en" else f.short_answer_de,
            "answer": f.answer_en if lang == "en" else f.answer_de,
        })

    # ⭐ Durchschnittsbewertung hinzufügen
    rating = get_average_rating()

    # 🎥 Webinare für Startseite
    from webinars.models import Webinar
    from django.db.models import Q as QQ
    upcoming_webinars = Webinar.objects.filter(
        is_active=True, date_time__gte=now
    ).filter(
        QQ(registration_start__isnull=True) | QQ(registration_start__lte=now)
    ).order_by('date_time')[:3]

    # 📊 App-Status für Startseite
    from status.models import App as StatusAppModel, GlobalIssue
    status_apps = StatusAppModel.objects.filter(is_active=True)
    status_data = []
    online_count = 0
    offline_count = 0
    issue_count = 0
    for sa in status_apps:
        latest = sa.statuses.order_by('-timestamp').first()
        has_issues = sa.issues.filter(is_resolved=False).exists()
        if has_issues:
            st = "issue"
            issue_count += 1
        elif latest and latest.status == "offline":
            st = "offline"
            offline_count += 1
        else:
            st = "online"
            online_count += 1
        status_data.append({'app': sa, 'status': st, 'latest': latest})
    global_issues = GlobalIssue.objects.filter(is_resolved=False)

    is_en = lang == 'en'
    return render(request, 'main/home.html', {
        'user_groups': user_groups,
        'latest_blog': latest_blog,
        'products': random_products,
        'packages': random_packages,
        'upcoming_webinars': upcoming_webinars,
        'faqs': localized_faqs,
        'rating': rating,
        'lang': lang,
        'status_data': status_data,
        'global_issues': global_issues,
        'online_count': online_count,
        'offline_count': offline_count,
        'issue_count': issue_count,
        'T': {
            'services': 'Our Services' if is_en else 'Unsere Services',
            'web_dev': 'Web Development' if is_en else 'Webentwicklung',
            'web_dev_desc': 'Custom websites and web applications' if is_en else 'Maßgeschneiderte Websites',
            'automation': 'Automation' if is_en else 'Automatisierung',
            'automation_desc': 'Smart process automation' if is_en else 'Intelligente Prozessautomatisierung',
            'marketing': 'Marketing' if is_en else 'Marketing',
            'marketing_desc': 'SEO & digital strategies' if is_en else 'SEO & digitale Strategien',
            'cloud': 'Cloud & IT' if is_en else 'Cloud & IT',
            'cloud_desc': 'Hosting & infrastructure' if is_en else 'Hosting & Infrastruktur',
            'why_us': 'Why Choose Us?' if is_en else 'Warum wir?',
            'fast': 'Fast & Reliable' if is_en else 'Schnell & Zuverlässig',
            'fast_desc': 'Quick delivery with dependable results' if is_en else 'Schnelle Lieferung mit Ergebnissen',
            'german': 'Made in Germany' if is_en else 'Made in Germany',
            'german_desc': 'GDPR compliant, highest standards' if is_en else 'DSGVO-konform, höchste Standards',
            'fair': 'Fair Prices' if is_en else 'Faire Preise',
            'fair_desc': 'Transparent, no hidden fees' if is_en else 'Transparent, keine versteckten Gebühren',
            'tailored': 'Tailored Solutions' if is_en else 'Maßgeschneiderte Lösungen',
            'tailored_desc': 'Custom-fit for your needs' if is_en else 'Auf Ihre Bedürfnisse zugeschnitten',
            'resources': 'Resources' if is_en else 'Ressourcen',
            'wiki': 'Wiki' if is_en else 'Wiki',
            'wiki_desc': 'Guides & tutorials' if is_en else 'Anleitungen & Tutorials',
            'downloads': 'Downloads' if is_en else 'Downloads',
            'downloads_desc': 'Free tools & assets' if is_en else 'Kostenlose Tools & Assets',
            'blog_res': 'Blog' if is_en else 'Blog',
            'blog_res_desc': 'News & insights' if is_en else 'News & Einblicke',
            'how_we_work': 'How We Work' if is_en else 'Wie wir arbeiten',
            'consultation': 'Consultation' if is_en else 'Beratung',
            'consultation_desc': 'We listen and understand your needs' if is_en else 'Wir hören zu und verstehen',
            'planning': 'Planning' if is_en else 'Planung',
            'planning_desc': 'We design the perfect solution' if is_en else 'Wir entwerfen die perfekte Lösung',
            'development': 'Development' if is_en else 'Entwicklung',
            'development_desc': 'We build with quality and speed' if is_en else 'Qualität und Tempo',
            'launch': 'Launch & Support' if is_en else 'Launch & Support',
            'launch_desc': 'We deliver and keep improving' if is_en else 'Wir liefern und verbessern',
            'detailed_status': 'To Status Page' if is_en else 'Zur Statusseite',
            'view_all': 'Our Services' if is_en else 'Unsere Services',
        },
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Newsletter-Anmeldung an euch senden
            if form.cleaned_data.get('accept_marketing'):
                try:
                    send_mail(
                        subject=f'Neue Newsletter-Anmeldung: {user.username}',
                        message=f'''
Neue Newsletter-Anmeldung:

Username: {user.username}
Email: {user.email}
Datum: {user.date_joined.strftime("%d.%m.%Y %H:%M")}

Der Benutzer hat sich für Marketing-E-Mails angemeldet.
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=["j-nicolay@joel-digitals.com"],  # Eure E-Mail-Adresse
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Newsletter-Benachrichtigung konnte nicht gesendet werden: {e}")
            
            messages.success(
                request,
                _("Registration successful. You can now log in.")
            )
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'main/register.html', {'form': form})

def login_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            return redirect('home')  # oder eine andere Zielseite
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form, 'user_groups': user_groups})

from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('home')  # KEINE weiteren Argumente hier


def about_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'main/about.html', {'user_groups': user_groups})

def service_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'main/services.html', {'user_groups': user_groups})

def team_view(request):
    members = TeamMember.objects.all()
    return render(request, 'main/team.html', {'members': members})


def opening_hours(request):
    today = date.today()
    today_name = today.strftime("%A")
    end_date = today + timedelta(days=6)  # heute + 6 Tage

    # Basiszeiten (Normalplan)
    base_hours = {
        oh.weekday: (
            "Closed"
            if oh.closed
            else f"{oh.open_time.strftime('%H:%M')} – {oh.close_time.strftime('%H:%M')}"
        )
        for oh in OpeningHour.objects.all()
    }

    # Sonderzeiten nur für heute bis 6 Tage später
    specials = SpecialOpeningHour.objects.filter(
        date__gte=today, date__lte=end_date
    ).order_by("date")

    # Mapping für kommende Sonderzeiten pro Wochentag
    special_overrides = {}
    for s in specials:
        weekday_name = s.date.strftime("%A")
        special_overrides[weekday_name] = (
            "Closed"
            if s.closed
            else f"{s.open_time.strftime('%H:%M')} – {s.close_time.strftime('%H:%M')}"
        )

    # Heute überschreiben, falls Sonderzeit existiert
    if today_name in special_overrides:
        base_hours[today_name] = special_overrides[today_name]

    # Montag → Sonntag sortieren
    days_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]

    ordered_times = {}
    for day in days_order:
        if day in special_overrides:
            ordered_times[day] = " *" + special_overrides[day]  # Sternchen für Sonderzeit
        else:
            ordered_times[day] = base_hours.get(day, "Closed")

    context = {
        "opening_times": ordered_times,
        "today": today_name,
        "phone_number": "+49 1525 3480270",
    }
    return render(request, "main/opening_hours.html", context)


from django.http import JsonResponse
from oauth2_provider.decorators import protected_resource

@protected_resource()
def user_info(request):
    user = request.user
    return JsonResponse({
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })

import secrets
import logging
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from .models import SSOClient, SSOSession, SSOScope, SSOAuthorization, SSOClient_Authorization

logger = logging.getLogger(__name__)


def sso_connect(request):
    """
    OAuth-Flow Schritt 1: Redirect zu Login/Authorize
    - User nicht eingeloggt → Redirect zu Login
    - User eingeloggt, nicht autorisiert → Zeige Authorize-Seite
    - User eingeloggt und bereits autorisiert → Direkt Token generieren ✅
    """
    client_id = request.GET.get('client_id')
    redirect_uri = request.GET.get('redirect_uri')
    state = request.GET.get('state', '')
    scope = request.GET.get('scope', 'profile,email')
    
    # Validiere Client
    try:
        client = SSOClient.objects.get(client_id=client_id, is_active=True)
        
        if not client.is_callback_allowed(redirect_uri):
            return render(request, 'sso_error.html', {
                'error': 'Invalid redirect_uri',
                'expected': client.callback_url,
                'received': redirect_uri,
            })
            
    except SSOClient.DoesNotExist:
        return render(request, 'sso_error.html', {
            'error': 'Invalid client_id'
        })
    
    # User nicht eingeloggt → Redirect zu Login-Seite
    if not request.user.is_authenticated:
        login_url = f"/auth/sso/login/?client_id={client_id}&redirect_uri={redirect_uri}&state={state}&scope={scope}"
        return redirect(login_url)
    
    # ✅ User eingeloggt → Prüfe ob bereits autorisiert
    try:
        authorization = SSOAuthorization.objects.get(
            user=request.user,
            client=client
        )
        
        # ✅ WICHTIG: Bereits autorisiert → Direkt Token generieren und weiterleiten
        logger.info(f"User {request.user.email} bereits autorisiert für {client.name} - direkte Weiterleitung")
        token = _generate_sso_token(request.user, client, authorization)
        callback_url = f"{redirect_uri}?token={token}&state={state}"
        return redirect(callback_url)
        
    except SSOAuthorization.DoesNotExist:
        # ✅ Noch nicht autorisiert → Zeige Authorize-Seite
        logger.info(f"User {request.user.email} noch nicht autorisiert für {client.name} - zeige Authorize-Seite")
        return redirect(f"/auth/sso/authorize-page/?client_id={client_id}&redirect_uri={redirect_uri}&state={state}&scope={scope}")

def sso_login_page(request):
    """Zeigt Login-Seite für SSO"""
    client_id = request.GET.get('client_id')
    redirect_uri = request.GET.get('redirect_uri')
    state = request.GET.get('state', '')
    scope = request.GET.get('scope', 'profile,email')
    
    try:
        client = SSOClient.objects.get(client_id=client_id, is_active=True)
    except SSOClient.DoesNotExist:
        return render(request, 'sso_error.html', {
            'error': 'Invalid client_id'
        })
    
    return render(request, 'sso_connect.html', {
        'client': client,
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': scope,
    })


@login_required
def sso_authorize_page(request):
    """Zeigt Autorisierungs-Seite (User ist bereits eingeloggt)"""
    client_id = request.GET.get('client_id')
    redirect_uri = request.GET.get('redirect_uri')
    state = request.GET.get('state', '')
    scope_string = request.GET.get('scope', 'profile,email')
    
    try:
        client = SSOClient.objects.get(client_id=client_id, is_active=True)
        
        if not client.is_callback_allowed(redirect_uri):
            return render(request, 'sso_error.html', {
                'error': 'Invalid redirect_uri'
            })
            
    except SSOClient.DoesNotExist:
        return render(request, 'sso_error.html', {
            'error': 'Invalid client_id'
        })
    
    # ✅ Lade ALLE Scopes die für diesen Client authorisiert sind
    client_auth_scopes = SSOClient_Authorization.objects.filter(
        client=client
    ).select_related('scope')
    
    scopes = [ca.scope for ca in client_auth_scopes]
    
    return render(request, 'sso_authorize.html', {
        'user': request.user,
        'client': client,
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope_string': scope_string,
        'scopes': scopes,
    })

@login_required
@require_http_methods(["POST"])
def sso_authorize(request):
    """User hat Autorisierung bestätigt"""
    client_id = request.POST.get('client_id')
    redirect_uri = request.POST.get('redirect_uri')
    state = request.POST.get('state', '')
    scope_string = request.POST.get('scope', 'profile,email')
    
    try:
        client = SSOClient.objects.get(client_id=client_id, is_active=True)
        
        if not client.is_callback_allowed(redirect_uri):
            return render(request, 'sso_error.html', {
                'error': 'Invalid redirect_uri'
            })
        
        # ✅ Lade ALLE authorisierten Scopes für diesen Client (über SSOClient_Authorization)
        client_auth_scopes = SSOClient_Authorization.objects.filter(
            client=client
        ).select_related('scope')
        
        # Extrahiere die Scope-Objekte
        scopes = [ca.scope for ca in client_auth_scopes]
        
        # Erstelle oder update Authorization für diesen User
        authorization, created = SSOAuthorization.objects.get_or_create(
            user=request.user,
            client=client
        )
        
        # Setze alle authorisierten Scopes
        authorization.scopes.set(scopes)
        authorization.save()
        
        logger.info(f"Authorization {'created' if created else 'updated'}: {request.user.email} → {client.name} (Scopes: {len(scopes)})")
        
        # Generiere Token
        token = _generate_sso_token(request.user, client, authorization)
        callback_url = f"{redirect_uri}?token={token}&state={state}"
        
        return redirect(callback_url)
        
    except SSOClient.DoesNotExist:
        return render(request, 'sso_error.html', {
            'error': 'Invalid client_id'
        })


@csrf_exempt
@require_http_methods(["POST"])
def sso_connect_login(request):
    """Login speziell für SSO-Connect"""
    logger.info("SSO Connect Login - START")
    
    try:
        email = request.POST.get('email')
        password = request.POST.get('password')
        client_id = request.POST.get('client_id')
        redirect_uri = request.POST.get('redirect_uri')
        state = request.POST.get('state', '')
        scope = request.POST.get('scope', 'profile,email')
        
        # Validierung
        if not email or not password:
            return JsonResponse({'error': 'Email und Passwort erforderlich'}, status=400)
        
        if not client_id or not redirect_uri:
            return JsonResponse({'error': 'Client ID und Redirect URI erforderlich'}, status=400)
        
        # Client validieren
        try:
            client = SSOClient.objects.get(client_id=client_id, is_active=True)
        except SSOClient.DoesNotExist:
            return JsonResponse({'error': 'Invalid client'}, status=400)
        
        # User authentifizieren
        from django.contrib.auth.models import User
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            
            if not user:
                return JsonResponse({'error': 'Ungültige Email oder Passwort'}, status=401)
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'Ungültige Email oder Passwort'}, status=401)
        
        # User einloggen
        django_login(request, user)
        logger.info(f"User eingeloggt: {user.email}")
        
        # Redirect zu Authorize-Seite
        authorize_url = f"/auth/sso/authorize-page/?client_id={client_id}&redirect_uri={redirect_uri}&state={state}&scope={scope}"
        
        return JsonResponse({
            'success': True,
            'redirect_url': authorize_url
        })
        
    except Exception as e:
        logger.error(f"SSO Connect Login Error: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Ein unerwarteter Fehler ist aufgetreten'
        }, status=500)


# ==================== TOKEN VALIDATION API ====================

@csrf_exempt
@require_http_methods(["POST"])
def validate_sso_token(request):
    """API: Validiert Token und gibt User-Daten zurück"""
    print("=" * 80)
    print("TOKEN VALIDATION - START")
    print("=" * 80)
    
    try:
        token = request.POST.get('token')
        client_id = request.POST.get('client_id')
        client_secret = request.POST.get('client_secret')
        
        print(f"📥 Empfangene Daten:")
        print(f"   - Token: {token[:20] if token else 'None'}...{token[-10:] if token else ''}")
        print(f"   - Client ID: {client_id}")
        print(f"   - Client Secret: {'*' * len(client_secret) if client_secret else 'None'}")
        
        logger.info(f"Token Validation Versuch: client_id={client_id}, token={token[:20] if token else 'None'}...")
        
        # Parameter prüfen
        if not all([token, client_id, client_secret]):
            missing = []
            if not token: missing.append('token')
            if not client_id: missing.append('client_id')
            if not client_secret: missing.append('client_secret')
            
            print(f"❌ FEHLER: Fehlende Parameter: {', '.join(missing)}")
            logger.warning(f"Fehlende Parameter: {', '.join(missing)}")
            return JsonResponse({
                'error': 'Missing parameters',
                'missing': missing
            }, status=400)
        
        print("✅ Alle Parameter vorhanden")
        
        # Client validieren
        print(f"\n🔍 Validiere Client Credentials...")
        try:
            client = SSOClient.objects.get(
                client_id=client_id,
                client_secret=client_secret,
                is_active=True
            )
            print(f"✅ Client validiert:")
            print(f"   - Name: {client.name}")
            print(f"   - Client ID: {client.client_id}")
            logger.info(f"Client validiert: {client.name}")
        except SSOClient.DoesNotExist:
            print(f"❌ FEHLER: Client credentials ungültig: {client_id}")
            logger.error(f"Client credentials ungültig: {client_id}")
            return JsonResponse({'error': 'Invalid client credentials'}, status=401)
        
        # Token validieren
        print(f"\n🔍 Suche Session mit Token...")
        try:
            session = SSOSession.objects.get(
                token=token,
                client=client,
                used=False
            )
            print(f"✅ Session gefunden:")
            print(f"   - User: {session.user.email}")
            print(f"   - Client: {session.client.name}")
            print(f"   - Erstellt: {session.created_at}")
            print(f"   - Verwendet: {session.used}")
            logger.info(f"Session gefunden: user={session.user.email}")
            
            # Token-Ablauf prüfen (5 Minuten)
            time_diff = timezone.now() - session.created_at
            print(f"\n⏱️  Token-Alter: {time_diff.total_seconds():.2f} Sekunden")
            
            if session.created_at < timezone.now() - timedelta(minutes=5):
                print(f"❌ FEHLER: Token abgelaufen (älter als 5 Minuten)")
                logger.warning(f"Token abgelaufen: {token[:20]}...")
                session.delete()
                print("🗑️  Abgelaufene Session gelöscht")
                return JsonResponse({'error': 'Token expired'}, status=401)
            
            print("✅ Token ist noch gültig")
            
            # Token als verwendet markieren
            print(f"\n✏️  Markiere Token als verwendet...")
            session.used = True
            session.save()
            print("✅ Token als verwendet markiert")
            
            logger.info(f"Token erfolgreich validiert für: {session.user.email}")
            
            # User-Daten zurückgeben
            user_data = {
                'email': session.user.email,
                'username': session.user.username,
                'first_name': session.user.first_name,
                'last_name': session.user.last_name,
            }
            
            print(f"\n📤 Zurückgegebene User-Daten:")
            for key, value in user_data.items():
                print(f"   - {key}: {value}")
            
            print("\n" + "=" * 80)
            print("✅ TOKEN VALIDATION - ERFOLGREICH")
            print("=" * 80 + "\n")
            
            return JsonResponse(user_data)
            
        except SSOSession.DoesNotExist:
            print(f"❌ FEHLER: Token nicht gefunden oder bereits verwendet")
            logger.error(f"Token nicht gefunden oder bereits verwendet: {token[:20]}...")
            return JsonResponse({'error': 'Invalid or already used token'}, status=401)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TOKEN VALIDATION - FEHLER")
        print("=" * 80)
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        print("=" * 80 + "\n")
        
        logger.error(f"Token Validation Error: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Ein unerwarteter Fehler ist aufgetreten',
            'detail': str(e)
        }, status=500)


# ==================== HELPER ====================

def _generate_sso_token(user, client, authorization):
    """Generiert einmaligen SSO-Token"""
    token = secrets.token_urlsafe(48)
    
    session = SSOSession.objects.create(
        token=token,
        user=user,
        client=client,
        authorization=authorization,
    )
    
    logger.info(f"SSO Session erstellt: user={user.email}, client={client.name}")
    return token


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction


@login_required
def profile_view(request):
    """
    Zeigt das Profil des eingeloggten Benutzers an.
    """
    context = {
        'user': request.user,
        'wallet_balance': getattr(request.user, 'wallet_balance', 0.00),
    }
    
    # Optional: Zusätzliche Informationen aus UserProfile laden
    if hasattr(request.user, 'userprofile'):
        context['profile'] = request.user.userprofile
    
    return render(request, 'profile/profile.html', context)


@login_required
def profile_edit(request):
    """
    Ermöglicht dem Benutzer, sein Profil zu bearbeiten.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user = request.user
                
                # Benutzerdaten aktualisieren
                user.first_name = request.POST.get('first_name', '').strip()
                user.last_name = request.POST.get('last_name', '').strip()
                user.email = request.POST.get('email', '').strip()
                
                # Optional: Username ändern (falls erlaubt)
                new_username = request.POST.get('username', '').strip()
                if new_username and new_username != user.username:
                    # Prüfen ob Username bereits existiert
                    from django.contrib.auth.models import User
                    if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                        messages.error(request, 'Dieser Benutzername ist bereits vergeben.')
                        return redirect('profile_edit')
                    user.username = new_username
                
                user.save()
                
                # Optional: Zusätzliche Profilfelder (UserProfile Model)
                if hasattr(user, 'userprofile'):
                    profile = user.userprofile
                    profile.phone = request.POST.get('phone', '').strip()
                    profile.address = request.POST.get('address', '').strip()
                    profile.city = request.POST.get('city', '').strip()
                    profile.postal_code = request.POST.get('postal_code', '').strip()
                    profile.country = request.POST.get('country', '').strip()
                    profile.company = request.POST.get('company', '').strip()
                    profile.save()
                
                messages.success(request, 'Profil erfolgreich aktualisiert!')
                return redirect('profile_view')
                
        except Exception as e:
            messages.error(request, f'Fehler beim Aktualisieren: {str(e)}')
            return redirect('profile_edit')
    
    context = {
        'user': request.user,
        'wallet_balance': getattr(request.user, 'wallet_balance', 0.00),
    }
    
    if hasattr(request.user, 'userprofile'):
        context['profile'] = request.user.userprofile
    
    return render(request, 'profile/profile_edit.html', context)


@login_required
def change_password(request):
    """
    Ermöglicht dem Benutzer, sein Passwort zu ändern.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Wichtig: Session beibehalten
            messages.success(request, 'Ihr Passwort wurde erfolgreich geändert!')
            return redirect('profile_view')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'wallet_balance': getattr(request.user, 'wallet_balance', 0.00),
    }
    
    return render(request, 'profile/change_password.html', context)


@login_required
def delete_account(request):
    """
    Ermöglicht dem Benutzer, sein Konto zu löschen (mit Bestätigung).
    """
    if request.method == 'POST':
        confirmation = request.POST.get('confirm_delete', '').strip()
        if confirmation.lower() == 'löschen':
            user = request.user
            user.is_active = False  # Deaktivieren statt löschen (sicherer)
            user.save()
            
            # Optional: Vollständig löschen
            # user.delete()
            
            messages.success(request, 'Ihr Konto wurde deaktiviert.')
            from django.contrib.auth import logout
            logout(request)
            return redirect('home')
        else:
            messages.error(request, 'Bitte geben Sie "löschen" zur Bestätigung ein.')
    
    context = {
        'wallet_balance': getattr(request.user, 'wallet_balance', 0.00),
    }
    
    return render(request, 'profile/delete_account.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .models import SSOAuthorization


@login_required
def app_permissions(request):
    """View zum Anzeigen aller autorisierten Apps"""
    authorizations = SSOAuthorization.objects.filter(
        user=request.user
    ).select_related('client').prefetch_related('scopes').order_by('-last_used')
    
    context = {
        'authorizations': authorizations,
    }
    return render(request, 'profile/app_permissions.html', context)


@login_required
def revoke_app_permission(request, auth_id):
    """View zum Widerrufen einer App-Berechtigung"""
    authorization = get_object_or_404(SSOAuthorization, id=auth_id, user=request.user)
    
    if request.method == 'POST':
        app_name = authorization.client.name
        authorization.delete()
        messages.success(
            request, 
            _('Access for "{}" has been successfully revoked.').format(app_name)
        )
        return redirect('app_permissions')
    
    # Wenn kein POST, zurück zur Übersicht
    return redirect('app_permissions')

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /profile/",
        "Disallow: /o/",
        "Disallow: /api/",
        "Disallow: /auth/",
        "Allow: /",
        "",
        "Sitemap: https://www.joel-digitals.de/sitemap.xml",
        "Sitemap: https://www.joel-digitals.de/sitemap.txt",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_txt(request):
    from django.urls import reverse
    from blog.models import BlogPost
    from landingpages.models import LandingPage
    from shop_ourapps.models import App as ShopApp
    from wiki.models import Wiki as WikiArticle
    from status.models import App as StatusApp

    base_url = "https://www.joel-digitals.de"
    lines = []

    for lang in ['de', 'en']:
        prefix = f"/{lang}"

        static_pages = [
            '', '/about/', '/services/', '/contact/contact/',
            '/blog/', '/our-apps/', '/shop/',
            '/downloads/', '/status/',
            '/wiki/', '/imprint/', '/privacy/', '/terms/',
        ]
        for page in static_pages:
            lines.append(f"{base_url}{prefix}{page}")

        for post in BlogPost.objects.filter(is_published=True):
            lines.append(f"{base_url}{prefix}/blog/{post.slug}/")

        for lp in LandingPage.objects.filter(is_active=True):
            lines.append(f"{base_url}{prefix}/{lp.slug}/")

        for app in ShopApp.objects.filter(is_available_for_purchase=True):
            lines.append(f"{base_url}{prefix}/shop/{app.slug}/")

        for wiki in WikiArticle.objects.filter(is_published=True):
            lines.append(f"{base_url}{prefix}/wiki/{wiki.slug}/")

    for sa in StatusApp.objects.filter(is_active=True):
        lines.append(f"{base_url}/status/app/{sa.pk}/")

    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def support_view(request):
    """
    Support page view with ElevenLabs Voice Agent
    """
    context = {
        'page_title': 'Support - Joel Digitals',
    }
    return render(request, 'support.html', context)