#
# x509 authentication backend
# checking the user profile
#

from models import Profile
from django.contrib.auth import get_user_model


class X509Backend(object):
    """
    Authenticate using the X509 certificate in the profile
    """

    def authenticate(self, username=None, password=None, user_dn=None):
        if user_dn:
            try:
                profile = Profile.objects.get(user_dn=user_dn)
                if profile.user and profile.user.is_active:
                    return profile.user
            except (Profile.DoesNotExist, Profile.MultipleObjectsReturned):
                pass 
        return None

    def get_user(self, user_id):
        m = get_user_model()
        try:
            return m.objects.get(pk=user_id)
        except m.DoesNotExist:
            return None
