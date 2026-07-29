BACKROOM_GROUP_NAME = "Backroom"


def has_backroom_access(user):
    """Backroom ist ein EK-Shop: nur für Mitglieder der Backroom-Gruppe und Admins."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return user.groups.filter(name=BACKROOM_GROUP_NAME).exists()
