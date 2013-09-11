#
#
#

from django.core.urlresolvers import reverse, reverse_lazy
from django.core.mail import send_mail
from django.contrib.sites.models import RequestSite
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.template import loader

# authentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

# Class based views
from class_based_auth_views.views import LoginView, LogoutView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, UpdateView, DeleteView

from cloud_profiles.models import Profile
from cloud_profiles.forms import (RegisterCertForm, ProfileUpdateForm,
                                  RegisterForm, PasswordResetForm)


# Mixin for staff required views
class StaffView(object):
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(StaffView, self).dispatch(request, *args, **kwargs)


# Mixin for authentication required views
class AuthenticatedView(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AuthenticatedView, self).dispatch(request,
                                                       *args, **kwargs)


class UserLogin(LoginView):
    template_name = 'cloud_profiles/login.html'

    def dispatch(self, request, *args, **kwargs):
        if 'SSL_CLIENT_S_DN' in request.META:
            user = authenticate(user_dn=request.META['SSL_CLIENT_S_DN'])
            if user and user.is_active:
                login(request, user)
                return HttpResponseRedirect(self.get_success_url())
        return super(UserLogin, self).dispatch(request, *args, **kwargs)


class UserLogout(LogoutView):
    template_name = 'cloud_profiles/logout.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            logout(self.request)
        return super(UserLogout, self).get(*args, **kwargs)

    def get_redirect_url(self, **kwargs):
        return super(UserLogout, self).get_redirect_url(reverse('home'), **kwargs)


class ProfileView(AuthenticatedView, TemplateView):
    template_name = 'cloud_profiles/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)
        profile = None
        if 'pk' in kwargs:
            profile = get_object_or_404(Profile, pk=kwargs['pk'])
        else:
            user = self.request.user
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.profile_from_user(user)
        ctx['profile'] = profile
        ctx['selfie'] = profile == self.request.user.profile
        return ctx


class BaseProfileModify(AuthenticatedView, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm


class ProfileModify(BaseProfileModify):
    success_url = reverse_lazy('profiles')


class SelfProfileModify(BaseProfileModify):
    success_url = reverse_lazy('profile')

    def get_object(self, *args, **kwargs):
        return self.request.user.profile


class ProfileList(StaffView, ListView):
    model = Profile
    context_object_name = 'profiles'


class ProfileDel(StaffView, DeleteView):
    model = Profile
    success_url = reverse_lazy('profiles')


# confirm the registration from user
class ProfileConfirm(TemplateView):
    def notify_admins(self, profile):
        ctxt = {
            'site': RequestSite(self.request),
            'profile': profile,
        }
        body = loader.render_to_string('cloud_profiles/admin_notice_email.txt',
                                       ctxt).strip()
        subject = 'New ibercloud account registered'
        send_mail(subject, body, 'ibergrid cloud <support@ibergrid.eu>',
                  # XXX fix this
                  ['enolfc@ifca.unican.es', 'isabel@campos-it.es'])

    def get_context_data(self, **kwargs):
        confirmation_key = kwargs.get('confirmation_key', '')
        profile = get_object_or_404(Profile,
                                    confirmation_key=confirmation_key)
        if profile.confirm():
            self.notify_admins(profile)
            self.template_name = 'cloud_profiles/confirm_ok.html'
        else:
            self.template_name = 'cloud_profiles/confirm_failed.html'
        return super(ProfileConfirm, self).get_context_data(**kwargs)


# activate one user
class ProfileActivate(StaffView, RedirectView):
    permanent = False

    def send_password_reset_email(self, profile):
        ctxt = {
            'site': RequestSite(self.request),
            'profile': profile,
        }
        body = loader.render_to_string('cloud_profiles/activation_email.txt',
                                       ctxt).strip()
        subject = 'Your Ibercloud account is now active'
        send_mail(subject, body, 'ibergrid cloud <support@ibergrid.eu>',
                  [profile.email])


    def get_redirect_url(self, pk):
        redirect_url = reverse('profiles')
        profile = get_object_or_404(Profile, pk=pk)
        profile.activate()
        self.send_password_reset_email(profile)
        return redirect_url


class ResetPassword(FormView):
    template_name = 'cloud_profiles/reset_password.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('home')
    profile = None

    def get(self, request, *args, **kwargs):
        key = kwargs.get('password_key', '')
        get_object_or_404(Profile,
                          password_key=key,
                          status=Profile.VALID)
        return super(ResetPassword, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        key = kwargs.get('password_key', '')
        self.profile = get_object_or_404(Profile,
                                         password_key=key,
                                         status=Profile.VALID)
        return super(ResetPassword, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.profile:
            return redirect(reverse('profiles'))
        self.profile.password_reset(form.cleaned_data['new_password1'])
        return super(ResetPassword, self).form_valid(form)


class RegisterProfile(FormView):
    template_name = 'cloud_profiles/registration.html'
    form_class = RegisterForm
    model = Profile
    success_url = 'registration_ok'
    user_dn = None

    def send_confirmation_email(self, profile):
        ctxt = {
            'site': RequestSite(self.request),
            'profile': profile,
        }
        body = loader.render_to_string('cloud_profiles/registration_email.txt',
                                       ctxt).strip()
        subject = 'Ibercloud account confirmation'
        send_mail(subject, body, 'ibergrid cloud <support@ibergrid.eu>',
                  [profile.email])


    def form_valid(self, form):
        # fields not available in the cert form
        research_area = form.cleaned_data.get('research_area', '')
        description = form.cleaned_data.get('description', '')
        resources = form.cleaned_data.get('resources', '')
        # create the user
        p = Profile.objects.new_profile(name=form.cleaned_data['name'],
                                        email=form.cleaned_data['email'],
                                        phone=form.cleaned_data['phone'],
                                        institution=form.cleaned_data['institution'],
                                        country=form.cleaned_data['country'],
                                        research_area=research_area,
                                        description=description,
                                        resources=resources)
        if self.user_dn:
            p.user_dn = self.user_dn
        p.save()
        self.send_confirmation_email(p)
        return super(RegisterProfile, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['user_dn'] = self.user_dn
        return super(RegisterProfile, self).get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        if 'SSL_CLIENT_S_DN' in request.META:
            self.user_dn = request.META['SSL_CLIENT_S_DN']
            try:
                Profile.objects.get(user_dn=self.user_dn)
                self.template_name = 'cloud_profiles/registration_dup.html'
                return self.render_to_response(self.get_context_data())
            except Profile.DoesNotExist:
                pass
            self.form_class = RegisterCertForm
        return super(RegisterProfile, self).dispatch(request, *args, **kwargs)
