from django.contrib import admin
from piston.models import Nonce, Consumer, Token

admin.site.register(Nonce)
admin.site.register(Consumer)
admin.site.register(Token)
