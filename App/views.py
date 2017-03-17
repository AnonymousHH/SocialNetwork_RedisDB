from django.http import HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import redis


def enterPage(request):
    active = dict(register='', login='active')
    InActive = dict(register='', login='in')
    IdError = dict(register='hideRegister', login='hideLogin')
    return render(request, 'EnterPage.html', {'IdError': IdError, 'active': active, 'InActive': InActive})


def UserHomePage(request, UserId):
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    getUser = connection.hget('user', UserId)
    emailUser = str(getUser, 'utf-8')
    UserInfoTable = connection.hgetall(emailUser)
    UserInfo = dict()
    for k in UserInfoTable:
        key = str(k, 'utf-8')
        value = UserInfoTable[k]
        UserInfo[key] = str(value, 'utf-8')
    active = dict(home='active', profile='')
    return render(request, 'home.html', {'UserInfo': UserInfo, 'active': active})


@csrf_exempt
@require_POST
def Login(request):
    emailInput = request.POST['email']
    passwordInput = request.POST['pwd']
    UserId = 0
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    if connection.hset(emailInput, 'password', passwordInput):
        connection.hdel(emailInput)
        active = dict(register='', login='active')
        InActive = dict(register='', login='in')
        IdError = dict(register='hideRegister', login='showLogin')
        return render(request, 'EnterPage.html', {'IdError': IdError, 'active': active, 'InActive': InActive})
    else:
        userTable = connection.hgetall('user')
        for key in userTable:
            value = userTable[key]
            stringValue = str(value, 'utf-8')
            if stringValue == emailInput:
                UserId = str(key, 'utf-8')
                break
        return HttpResponseRedirect('/UserHomePage/' + UserId)
    pass


@csrf_exempt
@require_POST
def Register(request):
    name = request.POST['name']
    family = request.POST['family']
    email = request.POST['email']
    password = request.POST['pwd']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    PostTableName = 'postTable' + email
    FriendTableName = 'FriendTable' + email
    BlockUserTableName = 'BlockUserTable' + email
    if connection.hset(email, 'name', name) and connection.hset(email, 'family', family) and \
            connection.hset(email, 'password', password) and connection.hset(email, 'PostTable', PostTableName) and \
            connection.hset(email, 'FriendTable', FriendTableName) and \
            connection.hset(email, 'BlockUserTable', BlockUserTableName):
        UserListLen = connection.hlen('user')
        Id = UserListLen + 1
        connection.hset('user', Id, email)
        UserId = str(Id)
        return HttpResponseRedirect('/UserHomePage/' + UserId)
    else:
        active = dict(register='active', login='')
        InActive = dict(register='in', login='')
        IdError = dict(register='showRegister', login='hideLogin')
        return render(request, 'EnterPage.html', {'IdError': IdError, 'active': active, 'InActive': InActive})

    pass
