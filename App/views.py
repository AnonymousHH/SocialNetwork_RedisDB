from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import redis


def enterPage(request):
    page = loader.get_template('EnterPage.html')
    return HttpResponse(page.render())


@csrf_exempt
@require_POST
def Login(request):
    emailInput = request.POST['email']
    passwordInput = request.POST['pwd']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    pass


@csrf_exempt
@require_POST
def Register(request):
    name = request.POST['name']
    family = request.POST['family']
    email = request.POST['email']
    password = request.POST['pwd']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    if connection.hset(email, 'name', name) and connection.hset(email, 'family', family) and connection.hset(email,
                                                                                                             'password',
                                                                                                             password):
        massage = dict(dataPass='login complete')
        return render(request, 'home.html', {'messageRegister': massage})
    else:
        massage = dict(ErrorRegister='login not complete')
        return render(request, 'EnterPage.html', {'messageRegister': massage})
    pass


def home(request):
    page = loader.get_template('home.html')
    return HttpResponse(page.render())


@csrf_exempt
@require_POST
def your_name(request):
    name = request.POST['name']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    connection.set('name', name)
    massage = connection.get('name')
    string = str(massage, 'utf-8')
    return HttpResponse("Hello %s" % string)

