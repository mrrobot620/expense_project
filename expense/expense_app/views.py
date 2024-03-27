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

    if request.method != 'POST':
        form = TransactionForm()
        return render(request, 'home.html', {'form': form, 'balance': current_user, 'users': users})

    form = TransactionForm(request.POST)
   
    total_amount = int(request.POST.get("total_amount", 0))
    receivers = request.POST.getlist('receiver')
    amounts = [(amount) for amount in request.POST.getlist('amount')]
    description = request.POST.get('description')

    print(f"Amounts == {amounts}")

    
    # For Percentage wise spliting

    try:
        if '%' in amounts[0]:
            try:
                percentages = [float(amount.strip('%')) for amount in amounts]
                total_percentage = sum(percentages)
                if total_percentage != 100:
                    messages.error(request, 'Total percentage should be 100%.')
                    return redirect('home')

                amounts = [(percentage / 100) * total_amount for percentage in percentages]
                print(f"Amounts after Percent => {amounts}")

                for receiver , amount in zip(receivers , amounts):
                    form_instance = TransactionForm()
                    transaction = form_instance.save(commit=False)
                    transaction.sender = request.user
                    transaction.receiver = User.objects.get(pk=receiver)
                    transaction.amount = amount
                    transaction.description = description
                    transaction.save()
                messages.success(request, f'Expenses split successfully.', {'tag': "success"})
                return redirect('home')

            except ValueError:
                messages.error(request, 'Invalid percentage format.')
                return redirect('home')
    except Exception as e:
        print(e)
    finally:
        amounts = [int(amount) for amount in request.POST.getlist('amount')]

    # For equally Splitting
        
    if sum(amounts) == 0 and len(receivers) >= 2:
        equal_amount = total_amount / len(receivers)
        equal_amount = round(equal_amount, 2)
        print(f"Splitted Value => {equal_amount}")
        for receiver in receivers:
            form_instance = TransactionForm()
            transaction = form_instance.save(commit=False)
            transaction.sender = request.user
            transaction.receiver = User.objects.get(pk=receiver)
            transaction.amount = equal_amount
            transaction.description = description
            transaction.save()
        messages.success(request, f'Expenses Split Equally successfully, Each {equal_amount}', {'tag': "success"})
        return redirect('home')
    
    

    if total_amount != sum(amounts):
        messages.error(request, "Total amount does not match the sum of participants' amounts.")
        return redirect('home')

    if len(receivers) != len(amounts):
        messages.error(request, 'Form data lengths are not consistent.')
        return redirect('home')
    
    # For Exact Splitting

    for receiver, amount in zip(receivers, amounts):
        form_instance = TransactionForm(request.POST)
        if not form_instance.is_valid():
            messages.error(request, 'Form is not valid. Please check your input.')
            return redirect('home')

        transaction = form_instance.save(commit=False)
        transaction.sender = request.user
        transaction.receiver = User.objects.get(pk=receiver)
        transaction.amount = amount
        transaction.description = description
        transaction.save()
    messages.success(request, 'Expenses split successfully.', {'tag': "success"})

    return redirect('home')

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
    
@login_required
def split_equally(request):
    if request.method == 'POST':
        total_amount = int(request.POST.get("total_amount", 0))
        selected_users = request.POST.getlist('receiver')
        description = request.POST.get('description')

        print(f"Selected Users => {selected_users}  Total Amount => {total_amount}")

        if not total_amount or not selected_users:
            messages.error(request, 'Total amount and receivers must be provided.')
            return redirect('home') 

        num_users = len(selected_users)
        if num_users == 1:
            messages.error(request, 'Select at least two users to split equally.')
            return redirect('home')

        amount_per_user = total_amount / num_users

        current_user = request.user
        for user_id in selected_users:
            if int(user_id) != current_user.id: 
                transaction = Transaction(sender=current_user, receiver_id=user_id, amount=amount_per_user, description=description)
                transaction.save()

        messages.success(request, 'Expenses split equally among selected users.')
        return redirect('home') 

    else:
        messages.error(request, 'Invalid request method.')
        return redirect('home') 