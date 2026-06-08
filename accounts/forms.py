from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'full_name', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'full_name', 'role', 'is_2fa_enabled')

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email']

class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[('volunteer', 'Волонтёр'), ('vet', 'Ветеринар')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Роль'
    )
    confirmation_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Код подтверждения',
        help_text='Введите код для выбранной роли'
    )

    class Meta:
        model = User
        fields = ('username', 'role', 'password1', 'password2', 'confirmation_code')

    def clean_confirmation_code(self):
        role = self.cleaned_data.get('role')
        code = self.cleaned_data.get('confirmation_code')
        if role == 'volunteer' and code != 'VOL2026':
            raise forms.ValidationError('Неверный код подтверждения для роли Волонтёр')
        if role == 'vet' and code != 'VET2026':
            raise forms.ValidationError('Неверный код подтверждения для роли Ветеринар')
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user