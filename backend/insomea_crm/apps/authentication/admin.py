from django.contrib import admin

from .models.setupToken import SetupToken
from .models.passwordResetToken import PasswordResetToken


admin.site.register(SetupToken)
admin.site.register(PasswordResetToken)
