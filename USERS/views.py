'''
List of Views:
- REGISTER PAGE: To register a new user.
- LOGIN PAGE: To login a registered user.
- LOGOUT PAGE: To logout a registered user.
- ACOOUNT SETTINGS PAGE : To update profile pic and full name.
- VERDICT PAGE: Shows the verdict to the submission.
- SUBMISSIONS PAGE: To view all the submissions made by current logged-in user.

'''

from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_protect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes,force_str
#from .forms import UserForm, SubmissionForm


#from .tokens import account_activation_token
from USERS.models import User, Submission

from .forms import CreateUserForm
from datetime import datetime
from time import time

import os
import sys
import subprocess
from subprocess import PIPE
import os.path
import docker


###############################################################################################################################


# To register a new user
def registerPage(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data.get('email')
            if User.objects.filter(email=user_email).exists():
                messages.error(request,'Email already exist!')
                context = {'form': form}
                return render(request, 'register.html', context)

            user = form.save(commit=True)
            user.is_active = True
            user.save()
            messages.success(request, 'Account created successfully!')


            username = form.cleaned_data.get('username')
            current_site = get_current_site(request)
            
          #  email_subject = "Confirm your email!"
           # email_message = render_to_string('email_confirmation.html',{
            #    'name':username,
             #   'domain': current_site.domain,
              #  'uid':urlsafe_base64_encode(force_bytes(user.pk)),
               # 'token':account_activation_token.make_token(user),
            #})
           # to_email = form.cleaned_data.get('email')
          #  email = EmailMessage(
               # email_subject,
               # email_message,
              #  settings.EMAIL_HOST_USER,
             #   to=[to_email],
            #)
           # email.fail_silently = True
          #  email.send()

            return redirect('login')

    else:
        form = CreateUserForm()
    context = {'form': form}
    return render(request, 'register.html', context)
    
###############################################################################################################################


# To login a registered user
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.info(request, 'Username/Password is incorrect')

        context = {}
        return render(request, 'login.html', context)

###############################################################################################################################


# To logout a registered user
def logoutPage(request):
    logout(request)
    return redirect('login')


###############################################################################################################################
@login_required(login_url='login')
def allSubmissionPage(request):
    submissions = Submission.objects.filter(user=request.user.id)
    return render(request, 'submission.html', {'submissions': submissions})


   




