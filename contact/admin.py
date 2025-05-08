from django.contrib import admin
from .models import SalesWish, SupportTicket, TicketMessage, SalesEntry, SalesChatMessage

admin.site.register(SalesWish)
admin.site.register(SupportTicket)
admin.site.register(TicketMessage)
admin.site.register(SalesEntry)
admin.site.register(SalesChatMessage)