from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid1

import ldap_users

COUNTRIES = (
    ('ES', 'Spain'),
    ('PT', 'Portugal'),
)


class ProfileManager(models.Manager):
    def new_profile(self, *args, **kwargs):
        p = self.create(*args, **kwargs)
        model = get_user_model()
        defaults = {'is_active': False}
        p.user, created = model.objects.get_or_create(username=p.email,
                                                      defaults=defaults)
        if created:
            p.user.set_unusable_password()
            p.user.save()
        p.save()
        return p

    def profile_from_user(self, user):
        p = self.create(email=user.email,
                        name=user.username,
                        user=user)
        p.status = p.EXTERNAL
        p.save()
        return p


class Profile(models.Model):
    # custom manager
    objects = ProfileManager()
    # possible user status
    CREATED = 'CR'     # Created, needs activation from user
    CONFIRMED = 'CO'   # User has confirmed the creation
    VALID = 'VA'       # Admin has validated the user, can reset password
    ACTIVE = 'AC'      # User has set the password, "final" status
    EXTERNAL = 'EX'    # User is created externally, nothing to do
    STATUS = (
        (CREATED, 'Created'),
        (CONFIRMED, 'Confirmed'),
        (VALID, 'Valid'),
        (ACTIVE, 'Active'),
    )
    # fields
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    institution = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=3, choices=COUNTRIES,
                               default='ES', blank=True)
    # cert of user
    user_dn = models.CharField(max_length=100, blank=True)
    # Additional info for no cert users
    research_area = models.CharField(max_length=50, blank=True)
    description = models.TextField(help_text="Describe briefly the scientific "
                                             "problem and the computational "
                                             "methodology you intend to apply",
                                   blank=True)
    resources = models.TextField(help_text="Describe briefly the "
                                           "resources needed",
                                 blank=True)
    # the validation request code, (generated when the user is created)
    confirmation_key = models.CharField(max_length=100, default=uuid1())
    password_key = models.CharField(max_length=100, default=uuid1())
    # status of the profile
    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)
    # the django user
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                null=True, blank=True)

    def __unicode__(self):
        return self.email

    def get_dn(self):
        return 'uid=%s,ou=users,c=es,o=cloud,dc=ibergrid,dc=eu' % str(self.email)

    def get_uid(self):
        if self.country == 'ES':
            base = 1000000
        elif self.country == 'PS':
            base = 2000000
        else:
            base = 9000000
        return base + self.pk

    def check_password(self, passwd):
        return ldap_users.check_user_password(self.get_dn(), passwd)

    def update_password(self, old, new):
        ldap_users.change_user_password(self.get_dn(), old, new)

    def password_reset(self, password):
        if self.status != self.VALID:
            return
        ldap_users.reset_user_password(self.get_dn(), password)
        self.status = self.ACTIVE
        self.save()

    def activate(self):
        ldap_users.create_user(self.get_dn(), self.email,
                               self.name, self.get_uid())
        self.status = self.VALID
        self.user.is_active = True
        self.user.save()
        self.save()

    def confirm(self):
        if self.status != self.CREATED:
            return False
        self.status = self.CONFIRMED
        self.save()
        return True

    def delete(self, *args, **kwargs):
        if self.status in [self.VALID, self.ACTIVE]:
            ldap_users.delete_user(self.get_dn())
        super(Profile, self).delete(*args, **kwargs)

    def can_be_activated(self):
        return self.status in [self.CREATED, self.CONFIRMED]
