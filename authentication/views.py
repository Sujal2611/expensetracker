from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import account_activation_token
from django.db import transaction
from django.contrib import auth


class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'emailerror': 'Email is invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'emailerror': 'Sorry, this email is already in use'}, status=409)
        return JsonResponse({'email_valid': True})


class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        if not str(username).isalnum():
            return JsonResponse({'usernameerror': 'Username should only contain letters and numbers'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'usernameerror': 'Sorry, this username is already in use'}, status=409)
        return JsonResponse({'username_valid': True})


class RegistrationView(View):
    def get(self, request):
        return render(request, 'authentication/register.html')

    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        context = {'fieldValues': request.POST}

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'authentication/register.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'authentication/register.html', context)

        if len(password) < 6:
            messages.error(request, 'Password too short')
            return render(request, 'authentication/register.html', context)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                user.is_active = False  # Keep inactive until email verification
                user.save()

                # Email activation setup
                email_subject = "Activate Your Account"
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(request).domain
                link = reverse('activate', kwargs={'uidb64': uidb64, 'token': account_activation_token.make_token(user)})
                activate_url = f'http://{domain}{link}'
                email_body = f'Hi {user.username},\n\nPlease use this link to verify your account:\n{activate_url}'

                email_message = EmailMessage(
                    email_subject, email_body, 'Upadhyaysujal007@gmail.com', [email]
                )
                email_message.send(fail_silently=False)

                messages.success(request, 'Account created successfully. A verification email has been sent.')
                return redirect('login')
        
        except Exception as e:
            messages.error(request, f"Error occurred: {str(e)}")

        return render(request, 'authentication/register.html', context)


class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if not username or not password:
            messages.error(request, "Please fill in all fields")
            return render(request, "authentication/login.html")

        user = auth.authenticate(username=username, password=password)

        if user:
            if user.is_active:
                auth.login(request, user)
                messages.success(request, f"Welcome, {user.username}! You are now logged in.")
                return redirect('expenses')  # Redirect to dashboard
            else:
                messages.error(request, 'Account is not activated. Check your email for the activation link.')
                return redirect('login')  # Redirect to login page

        messages.error(request, "Invalid credentials, try again")
        return render(request, "authentication/login.html")


class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            if user.is_active:
                messages.info(request, "User already activated")
                return redirect('login')

            if not account_activation_token.check_token(user, token):
                messages.error(request, "Invalid activation link")
                return redirect('login')

            user.is_active = True
            user.save()
            messages.success(request, "Account activated successfully! You can now log in.")
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "Invalid activation request")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Activation failed: {str(e)}")
            return redirect('login')


class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            auth.logout(request)
            messages.success(request, "You have been logged out successfully")
        return redirect('login')
    