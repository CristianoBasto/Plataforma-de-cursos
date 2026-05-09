from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, label='Nome')
    last_name = forms.CharField(max_length=50, label='Sobrenome')
    email = forms.EmailField(label='E-mail')
    tipo = forms.ChoiceField(
        choices=Profile.TIPO_CHOICES,
        label='Quero me cadastrar como',
        widget=forms.RadioSelect
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'tipo':
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(usuario=user)
            profile.tipo = self.cleaned_data['tipo']
            profile.save()
        return user


class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, label='Nome')
    last_name = forms.CharField(max_length=50, label='Sobrenome')
    email = forms.EmailField(label='E-mail')
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='Bio')
    foto = forms.ImageField(required=False, label='Foto de perfil')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['bio'].initial = self.instance.profile.bio

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(usuario=user)
            profile.bio = self.cleaned_data.get('bio', '')
            if self.cleaned_data.get('foto'):
                profile.foto = self.cleaned_data['foto']
            profile.save()
        return user