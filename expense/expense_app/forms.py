from django import forms
from django.contrib.auth.models import User  # Import User model
from .models import Transaction


class TransactionForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(queryset=User.objects.all(), empty_label="Select Receiver")

    class Meta:
        model = Transaction
        fields = (
            'receiver', 'amount', 'description',
        )
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Description'}),
        }
