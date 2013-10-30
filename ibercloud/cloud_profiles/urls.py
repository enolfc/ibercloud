from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy

# my views
from cloud_profiles.views import (UserLogin, UserLogout, ProfileView,
                                  SelfProfileModify, ProfileModify,
                                  ProfileList, ProfileDel, RegisterProfile,
                                  ProfileConfirm, ProfileActivate,
                                  ResetPassword, UserList)

# password change
from django.contrib.auth.views import password_change
from cloud_profiles.forms import PasswordChangeForm

# simple template views
from django.views.generic.base import TemplateView

urlpatterns = patterns('',
    # login
    url(r'^login$', UserLogin.as_view(), name='login'),
    url(r'^logout$', UserLogout.as_view(), name='logout'),
    # password management
    url(r'^passwd-change$', password_change,
        {'template_name': 'cloud_profiles/passwd_change.html',
         'password_change_form': PasswordChangeForm,
         'post_change_redirect': reverse_lazy('profile')},
         name='password_change'),
    # user profiles
    url(r'^profiles$', ProfileList.as_view(), name='profiles'),
    url(r'^profile$', ProfileView.as_view(), name='profile'),
    url(r'^profile/(?P<pk>\w+)$', ProfileView.as_view(), name='profile'),
    url(r'^profile-update$', SelfProfileModify.as_view(),
        name='profile-update'),
    url(r'^profile-update/(?P<pk>\w+)$', ProfileModify.as_view(),
        name='profile-update'),
    url(r'^profile-del/(?P<pk>\w+)$', ProfileDel.as_view(),
        name='profile-del'),
    # registration
    url(r'^registration$', RegisterProfile.as_view(), name='registration'),
    url(r'^registration_ok$',
        TemplateView.as_view(template_name='cloud_profiles/registration_ok.html'),
        name='registration_ok'),
    # confirmation of registration
    url(r'^confirm/(?P<confirmation_key>[-_\w]+)$', ProfileConfirm.as_view(),
        name='confirm'),
    # activate profile
    url(r'^activate/(?P<pk>\w+)$', ProfileActivate.as_view(), name='activate'),
    #url(r'^activate/(?P<activation_key>(\w|-)+)$', ProfileActivate.as_view(),
    #    name='activate'),
    #url(r'^validation_fail$',
    #    TemplateView.as_view(template_name='cloud_profiles/validation_fail.html'),
    #    name='validation_fail'),
    #url(r'^validation_ok$',
    #    TemplateView.as_view(template_name='cloud_profiles/validation_ok.html'),
    #    name='validation_ok'),
    # reset profile password
    url(r'^reset-password/(?P<password_key>[-_\w]+)$',
        ResetPassword.as_view(), name='reset-password'),
    # list ldap users 
    url(r'^user-list$', UserList.as_view(), name='user-list'),
)
