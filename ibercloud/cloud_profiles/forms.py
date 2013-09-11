from django.forms import ModelForm, ValidationError
from django.contrib.auth import forms as auth_forms

from cloud_profiles.models import Profile

class BaseProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ('name', 'email', 'phone', 'institution', 'country',
                  'research_area', 'description', 'resources')

    def __init__(self, *args, **kwargs):
        super(BaseProfileForm, self).__init__(*args, **kwargs)
        # xxlarge fields
        self.set_class_to_fields('input-xxlarge',
                                 ('description', 'resources'))
        # xlarge fields
        self.set_class_to_fields('input-xlarge',
                                 ('name', 'email', 'phone', 'institution',
                                  'research_area'))
        # By default, everything is required
        try:
            required = self.Meta.required
        except AttributeError:
            required = self.Meta.fields
        for f in required:
            if f in self.fields:
                self.fields[f].required = True

    def set_attr_to_fields(self, attr, value, fields):
        for f in fields:
            if f in self.fields:
                self.fields[f].widget.attrs[attr] = value

    def set_class_to_fields(self, css_class, fields):
        self.set_attr_to_fields('class', css_class, fields)


class RegisterCertForm(BaseProfileForm):
    class Meta:
        model = Profile
        fields = ('name', 'email', 'phone', 'institution', 'country')


class RegisterForm(BaseProfileForm):
    pass


class ProfileUpdateForm(BaseProfileForm):
    class Meta:
        model = Profile
        fields = ('name', 'phone', 'institution', 'country',
                  'research_area', 'description', 'resources')
        required = ('name', )


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    def clean_old_password(self):
        try:
            profile = self.user.profile
            old_password = self.cleaned_data["old_password"]
            if profile.check_password(old_password):
                return old_password
            else:
                raise ValidationError(
                    self.error_messages['password_incorrect'],
                    code='password_incorrect',
                )
        except Profile.DoesNotExist:
            return super(PasswordChangeForm, self).clean_old_password(*args, **kwargs)
        

    def save(self, *args, **kwargs):
        try:
            profile = self.user.profile
            profile.update_password(self.cleaned_data['old_password'],
                                    self.cleaned_data['new_password1'])
            return self.user
        except Profile.DoesNotExist:
            return super(PasswordChangeForm, self).save(*args, **kwargs)


class PasswordResetForm(auth_forms.SetPasswordForm):
    def __init__(self, *args, **kwargs):
        # no need for user here, we won't do save()
        super(PasswordResetForm, self).__init__(None, *args, **kwargs)
