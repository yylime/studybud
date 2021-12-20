from django.core.exceptions import RequestAborted
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls.conf import path
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm, MyUserCreatiionForm

# Create your views here.


def loginPage(request):

    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except:
            # just using this does not work, please define message in main.html
            messages.error(request, 'User does not exist')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'email or password does not exist')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    page = 'register'
    form = MyUserCreatiionForm()
    if request.method == 'POST':
        form = MyUserCreatiionForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # make sure username easier
            user.username = user.username.lower()
            user.save()
            # if signed up then login this
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "An error occured during registration.")
    context = {'page': page, 'form': form}
    return render(request, 'base/login_register.html', context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    topics = Topic.objects.all()[:5]
    # the count of rooms
    room_count = rooms.count()

    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q) |
                                           Q(body__icontains=q)
                                           )

    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,
               'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    # don't use messages as default name because of django will flash it on the screen
    # message_set get all message related to the current room.
    room_messages = room.message_set.all()

    participants = room.participants.all()

    if request.method == 'POST':
        # directly create a Message and insert it to database
        Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body'),
        )
        room.participants.add(request.user)
        return redirect('room', pk=pk)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):

    user = User.objects.get(id=pk)
    rooms = user.room_set.all()

    # ADD  toptics and message in profile
    topics = Topic.objects.all()
    room_messages = user.message_set.all()

    context = {'rooms': rooms, 'topics': topics, 'user': user,
               'room_messages': room_messages}

    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        form = RoomForm(request.POST)
        room = Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
        )
        room.participants.add(request.user)
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    # pasa a instance to form
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        # tell form what's different
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form': form, 'topics': topics, 'room':room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == "POST":
        user = UserForm(request.POST, request.FILES, instance=user)
        if user.is_valid:
            user.save()
            return redirect('home')
    return render(request, 'base/update_user.html', {'form':form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics':topics})

def activatyPage(request):
    room_messages = Message.objects.filter()
    return render(request, 'base/activity.html', {'room_messages':room_messages})