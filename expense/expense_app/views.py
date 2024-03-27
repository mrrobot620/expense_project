from django.shortcuts import render , HttpResponse , redirect
from django.conf import settings 
from django.contrib.auth import authenticate , login , logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from .models import Profile , Transaction
from .forms import TransactionForm
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum


@login_required
def home(request):
    current_user = request.user
    users = User.objects.all()
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            total_amount = int(request.POST.get("total_amount")) 
            receivers = request.POST.getlist('receiver')
            amounts = [int(amount) for amount in request.POST.getlist('amount')] 
            description = request.POST.get('description') 
            print(f"Receivers => {receivers} | Amounts => {amounts} | Description => {description}")
            if total_amount == sum(amounts):
                if len(receivers) == len(amounts):
                    for receiver, amount in zip(receivers, amounts):
                        form_instance = TransactionForm(request.POST)  
                        if form_instance.is_valid():
                            transaction = form_instance.save(commit=False)
                            transaction.sender = request.user
                            transaction.receiver = User.objects.get(pk=receiver)
                            transaction.amount = amount
                            transaction.description = description  
                            transaction.save()
                            print(f"Receiver {receiver}: saved {amount}")
                        else:
                            print("Form is not valid.")
                            messages.error(request, 'Form is not valid. Please check your input.')
                            return redirect('home')
                    messages.success(request, 'Expenses split successfully.' ,{'tag': "success"})
                    return redirect('home')
                else:
                    messages.error(request, 'Form data lengths are not consistent.')
                    return redirect('home')
            else:
                messages.error(request, 'Total amount does not match the sum of participants\' amounts.')
                return redirect('home')
        else:
            messages.error(request, 'Form is not valid. Please check your input.')
            return redirect('home')
    else:
        form = TransactionForm()
    return render(request, 'home.html', {'form': form, "balance": current_user , "users": users})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request , username=username , password=password)
        if user is not None:
            login(request , user)
            return redirect('home')
        else:
            return render(request , 'login.html' , {"error": "Invalid Username or Password"})
    return render(request , 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login_view')

def balance_view(request):
    current_user = request.user
    users = User.objects.all()
    user_balances = {}

    for user in users:
        received_transactions = Transaction.objects.filter(receiver=current_user, sender=user)
        sent_transactions = Transaction.objects.filter(sender=current_user, receiver=user)
        total_received = received_transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_sent = sent_transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_balance = total_received - total_sent
        total_balance = round(total_balance, 2)
        if total_balance != 0 and user != current_user:  # Add balance to the dictionary only if it's non-zero and not the current user
            user_balances[user] = total_balance
    print(user_balances)
    return render(request, "balance.html" , {'user_balances': user_balances})
    