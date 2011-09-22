from django.contrib import admin
from piston.models import Nonce, Consumer, Token

class ConsumerAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)

admin.site.register(Nonce)
admin.site.register(Consumer, ConsumerAdmin)
admin.site.register(Token)
