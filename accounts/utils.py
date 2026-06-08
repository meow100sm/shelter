from .models import AuditLog

def log_action(user, action, details=''):
    if user and user.is_authenticated:
        AuditLog.objects.create(user=user, action=action, details=details)