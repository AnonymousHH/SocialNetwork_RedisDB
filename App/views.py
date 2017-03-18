from django.http import HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import redis
import time


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
    key = 'UserId'
    UserInfo[key] = UserId

    PostTableName = 'PostTable' + emailUser
    AllPostToken = connection.lrange(PostTableName, 0, -1)
    PostInfo = [dict() for x in range(len(AllPostToken))]
    counter = 0
    for i in range(len(AllPostToken)):
        AllPostToken[i] = str(AllPostToken[i], 'utf-8')
        PostTable_byte = connection.hgetall(AllPostToken[i])
        PostTable = dict()
        for k in PostTable_byte:
            key = str(k, 'utf-8')
            value = PostTable_byte[k]
            PostTable[key] = str(value, 'utf-8')
        EmailOfWhoPostIt = PostTable['email']
        NameOfWhoPostIt_byte = connection.hget(EmailOfWhoPostIt, 'name')
        NameOfWhoPostIt = str(NameOfWhoPostIt_byte, 'utf-8')
        PostTopic = PostTable['topic']
        PostType = PostTable['PostType']
        PostBody = PostTable['body']
        tempDictionary = PostInfo[counter]
        tempDictionary['name'] = NameOfWhoPostIt
        tempDictionary['topic'] = PostTopic
        tempDictionary['body'] = PostBody
        tempDictionary['type'] = PostType
        tempDictionary['email'] = EmailOfWhoPostIt
        counter += 1

    active = dict(home='active', profile='')
    return render(request, 'home.html', {'UserInfo': UserInfo, 'active': active, 'PostInfo': PostInfo})


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
    UserPostTableName = 'UserPostTable' + email
    FriendTableName = 'FriendTable' + email
    UserBlockTableName = 'UserBlockTable' + email
    UserLikeTableName = 'UserLikeTable' + email
    if connection.hset(email, 'name', name) and connection.hset(email, 'family', family) and \
            connection.hset(email, 'password', password) and \
            connection.hset(email, 'UserPostTable', UserPostTableName) and \
            connection.hset(email, 'FriendTable', FriendTableName) and \
            connection.hset(email, 'UserBlockTable', UserBlockTableName) and \
            connection.hset(email, 'UserLikeTable', UserLikeTableName):
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


@csrf_exempt
@require_POST
def UserPost(request, UserId):
    PostTopic = request.POST['UserPostTopic']
    PostBody = request.POST['UserPostBody']
    PostType = request.POST['PostType']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    getUser = connection.hget('user', UserId)
    emailUser = str(getUser, 'utf-8')
    PostTableName = 'PostTable' + emailUser
    Timestamp = time.time()
    token = str(Timestamp) + emailUser
    connection.rpush(PostTableName, token)
    connection.hset(token, emailUser, PostTopic)
    connection.hset(token, 'email', emailUser)
    connection.hset(token, 'topic', PostTopic)
    connection.hset(token, 'body', PostBody)
    connection.hset(token, 'PostType', PostType)
    return HttpResponseRedirect('/UserHomePage/' + UserId)
