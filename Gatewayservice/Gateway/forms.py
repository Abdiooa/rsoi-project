from django import forms

class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(label='Name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Surname', widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label='Login', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class NewHotel(forms.Form):
    name = forms.CharField(label='Name:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(label='Country:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(label='City:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label='Address:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    stars = forms.IntegerField(label='stars:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    price = forms.IntegerField(label="Price:", widget=forms.TextInput(attrs={'class': 'form-control'}))
    # photo = forms.ImageField(label='Hotel Photos:', required=False)

class NewUser(forms.Form):
    name = forms.CharField(label='Name:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Surname', widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label='Username:', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email:', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    role = forms.ChoiceField(label='Role:', choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password:', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class DeleteHotel(forms.Form):
    hotelUid = forms.CharField(label='Hotel UUID:', widget=forms.TextInput(attrs={'class': 'form-control'}))
