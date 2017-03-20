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
        FamilyOfWhoPostIt_byte = connection.hget(EmailOfWhoPostIt, 'family')
        FamilyOfWhoPostIt = str(FamilyOfWhoPostIt_byte, 'utf-8')
        PostTopic = PostTable['topic']
        PostType = PostTable['PostType']
        PostBody = PostTable['body']
        tempDictionary = PostInfo[counter]
        tempDictionary['name'] = NameOfWhoPostIt
        tempDictionary['family'] = FamilyOfWhoPostIt
        tempDictionary['topic'] = PostTopic
        tempDictionary['body'] = PostBody
        tempDictionary['type'] = PostType
        tempDictionary['token'] = AllPostToken[i]
        CommentTableName = 'comment' + AllPostToken[i]
        CommentList_byte = connection.hgetall(CommentTableName)
        AllComment = [dict() for x in range(len(CommentList_byte))]
        CounterComment = 0
        for k in CommentList_byte:
            EmailOfWhoCommentIt = str(k, 'utf-8')
            CommentBody = CommentList_byte[k]
            NameOfWhoCommentIt_byte = connection.hget(EmailOfWhoCommentIt, 'name')
            NameOfWhoCommentIt = str(NameOfWhoCommentIt_byte, 'utf-8')
            CommentList = AllComment[CounterComment]
            CommentList['name'] = NameOfWhoCommentIt
            CommentList['body'] = str(CommentBody, 'utf-8')
            CounterComment += 1
        tempDictionary['comment'] = AllComment
        tempDictionary['numberOfComment'] = len(CommentList_byte)
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
    UserLikeTableName = 'UserLikeTable' + email
    if connection.hset(email, 'name', name) and connection.hset(email, 'family', family) and \
            connection.hset(email, 'password', password) and \
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
    getEmail = connection.hget('user', UserId)
    emailUser = str(getEmail, 'utf-8')
    PostTableName = 'PostTable' + emailUser
    OwnPostTableName = 'OwnPostTable' + emailUser
    FilterByTypePostTableName = PostType + 'PostTable' + emailUser
    FollowerTableName = 'FollowerTable' + emailUser
    Timestamp = time.time()
    token = str(Timestamp) + emailUser
    connection.rpush(PostTableName, token)
    connection.rpush(OwnPostTableName, token)
    connection.rpush(FilterByTypePostTableName, token)
    Follower_byte = connection.hgetall(FollowerTableName)
    Follower = dict()
    for k in Follower_byte:
        key = str(k, 'utf-8')
        value = Follower_byte[k]
        Follower[key] = str(value, 'utf-8')
    for key in Follower:
        emailFollower = Follower[key]
        FollowerPostTableName = 'PostTable' + emailFollower
        connection.rpush(FollowerPostTableName, token)
    connection.hset(token, emailUser, PostTopic)
    connection.hset(token, 'email', emailUser)
    connection.hset(token, 'topic', PostTopic)
    connection.hset(token, 'body', PostBody)
    connection.hset(token, 'PostType', PostType)
    return HttpResponseRedirect('/UserHomePage/' + UserId)


@csrf_exempt
@require_POST
def UserComment(request, UserId):
    token = request.POST['token']
    CommentBody = request.POST['CommentBody']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    getEmail = connection.hget('user', UserId)
    emailUser = str(getEmail, 'utf-8')
    commentTableName = 'comment' + token
    connection.hset(token, 'CommentTable', commentTableName)
    connection.hset(commentTableName, emailUser, CommentBody)
    return HttpResponseRedirect('/UserHomePage/' + UserId)


@csrf_exempt
@require_POST
def Search(request, UserId):
    SearchQuery = request.POST['search']
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    allUser_byte = connection.hgetall('user')
    allUser = dict()
    for k in allUser_byte:
        key = str(k, 'utf-8')
        value = allUser_byte[k]
        allUser[key] = str(value, 'utf-8')
    EmailCurrentUser_byte = connection.hget('user', UserId)
    EmailCurrentUser = str(EmailCurrentUser_byte, 'utf-8')
    BlockTableName = 'BlockTable' + EmailCurrentUser
    BlockList_byte = connection.hgetall(BlockTableName)
    BlockList = dict()
    for k in BlockList_byte:
        key = str(k, 'utf-8')
        value = BlockList_byte[k]
        BlockList[key] = str(value, 'utf-8')
    allInfoOfUser = [dict() for x in range(len(allUser))]
    allInfoOfUserFind = []
    CounterInfoUser = 0
    for ID in allUser:
        if UserId != ID and ID not in BlockList.keys():
            email = allUser[ID]
            UserName_byte = connection.hget(email, 'name')
            UserName = str(UserName_byte, 'utf-8')
            if SearchQuery == UserName:
                TempInfoDic = allInfoOfUser[CounterInfoUser]
                TempInfoDic['name'] = UserName
                FamilyName_byte = connection.hget(email, 'family')
                FamilyName = str(FamilyName_byte, 'utf-8')
                TempInfoDic['family'] = FamilyName
                TempInfoDic['DestinationUserId'] = ID
                CounterInfoUser += 1
    for i in range(CounterInfoUser):
        allInfoOfUserFind.append(allInfoOfUser[i])
    active = dict(home='', profile='')
    SourceUserId = dict(SourceID=UserId)
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
    return render(request, 'SearchPage.html',
                  {'allInfoOfUserFind': allInfoOfUserFind, 'active': active, 'UserInfo': UserInfo,
                   'SourceUserId': SourceUserId})


def MyProfile(request, UserId):
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
    FriendInfo = dict()
    FollowerTableName = 'FollowerTable' + emailUser
    FollowingTableName = 'FollowingTable' + emailUser
    Follower_byte = connection.hgetall(FollowerTableName)
    FollowerList = [dict() for x in range(len(Follower_byte))]
    CounterFollower = 0
    for k in Follower_byte:
        key = str(k, 'utf-8')
        Follower = FollowerList[CounterFollower]
        Follower['UserId'] = key
        value_byte = Follower_byte[k]
        email = str(value_byte, 'utf-8')
        name_byte = connection.hget(email, 'name')
        name = str(name_byte, 'utf-8')
        family_byte = connection.hget(email, 'family')
        family = str(family_byte, 'utf-8')
        Follower['name'] = name
        Follower['family'] = family
        CounterFollower += 1
    Following_byte = connection.hgetall(FollowingTableName)
    FollowingList = [dict() for x in range(len(Following_byte))]
    CounterFollowing = 0
    for k in Following_byte:
        key = str(k, 'utf-8')
        Following = FollowingList[CounterFollowing]
        Following['UserId'] = key
        value_byte = Following_byte[k]
        email = str(value_byte, 'utf-8')
        name_byte = connection.hget(email, 'name')
        name = str(name_byte, 'utf-8')
        family_byte = connection.hget(email, 'family')
        family = str(family_byte, 'utf-8')
        Following['name'] = name
        Following['family'] = family
        CounterFollowing += 1
    FriendInfo['FollowerLen'] = len(Follower_byte)
    FriendInfo['FollowingLen'] = len(Following_byte)
    FriendInfo['FollowerList'] = FollowerList
    FriendInfo['FollowingList'] = FollowingList

    OwnPostTableName = 'OwnPostTable' + emailUser
    AllPostToken = connection.lrange(OwnPostTableName, 0, -1)
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
        tempDictionary['token'] = AllPostToken[i]
        CommentTableName = 'comment' + AllPostToken[i]
        CommentList_byte = connection.hgetall(CommentTableName)
        AllComment = [dict() for x in range(len(CommentList_byte))]
        CounterComment = 0
        for k in CommentList_byte:
            EmailOfWhoCommentIt = str(k, 'utf-8')
            CommentBody = CommentList_byte[k]
            NameOfWhoCommentIt_byte = connection.hget(EmailOfWhoCommentIt, 'name')
            NameOfWhoCommentIt = str(NameOfWhoCommentIt_byte, 'utf-8')
            CommentList = AllComment[CounterComment]
            CommentList['name'] = NameOfWhoCommentIt
            CommentList['body'] = str(CommentBody, 'utf-8')
            CounterComment += 1
        tempDictionary['comment'] = AllComment
        tempDictionary['numberOfComment'] = len(CommentList_byte)
        counter += 1

    active = dict(home='', profile='active')
    return render(request, 'MyProfile.html',
                  {'UserInfo': UserInfo, 'active': active, 'PostInfo': PostInfo, 'FriendInfo': FriendInfo})


def Profile(request, UserId, DestinationUserId):
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

    getDestinationUser = connection.hget('user', DestinationUserId)
    emailDestinationUser = str(getDestinationUser, 'utf-8')
    UserInfoTableDestination = connection.hgetall(emailDestinationUser)
    UserInfoDestination = dict()
    for k in UserInfoTableDestination:
        key = str(k, 'utf-8')
        value = UserInfoTableDestination[k]
        UserInfoDestination[key] = str(value, 'utf-8')
    key = 'UserIdDestination'
    UserInfoDestination[key] = DestinationUserId

    FriendInfo = dict()
    FollowerTableName = 'FollowerTable' + emailDestinationUser
    FollowingTableName = 'FollowingTable' + emailDestinationUser
    Follower_byte = connection.hgetall(FollowerTableName)
    FollowerList = [dict() for x in range(len(Follower_byte))]
    CounterFollower = 0
    for k in Follower_byte:
        key = str(k, 'utf-8')
        Follower = FollowerList[CounterFollower]
        Follower['UserId'] = key
        value_byte = Follower_byte[k]
        email = str(value_byte, 'utf-8')
        name_byte = connection.hget(email, 'name')
        name = str(name_byte, 'utf-8')
        family_byte = connection.hget(email, 'family')
        family = str(family_byte, 'utf-8')
        Follower['name'] = name
        Follower['family'] = family
        CounterFollower += 1
    Following_byte = connection.hgetall(FollowingTableName)
    FollowingList = [dict() for x in range(len(Following_byte))]
    CounterFollowing = 0
    for k in Following_byte:
        key = str(k, 'utf-8')
        Following = FollowingList[CounterFollowing]
        Following['UserId'] = key
        value_byte = Following_byte[k]
        email = str(value_byte, 'utf-8')
        name_byte = connection.hget(email, 'name')
        name = str(name_byte, 'utf-8')
        family_byte = connection.hget(email, 'family')
        family = str(family_byte, 'utf-8')
        Following['name'] = name
        Following['family'] = family
        CounterFollowing += 1
    FriendInfo['FollowerLen'] = len(Follower_byte)
    FriendInfo['FollowingLen'] = len(Following_byte)
    FriendInfo['FollowerList'] = FollowerList
    FriendInfo['FollowingList'] = FollowingList

    FollowingUserIdTableName = 'FollowingTable' + emailUser
    if connection.hexists(FollowingUserIdTableName, DestinationUserId):
        OwnPostTableName = 'OwnPostTable' + emailDestinationUser
        FriendInfo['relation'] = 'UnFollow'
    else:
        OwnPostTableName = 'publicPostTable' + emailDestinationUser
        FriendInfo['relation'] = 'Follow'
    AllPostToken = connection.lrange(OwnPostTableName, 0, -1)
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
        tempDictionary['token'] = AllPostToken[i]
        CommentTableName = 'comment' + AllPostToken[i]
        CommentList_byte = connection.hgetall(CommentTableName)
        AllComment = [dict() for x in range(len(CommentList_byte))]
        CounterComment = 0
        for k in CommentList_byte:
            EmailOfWhoCommentIt = str(k, 'utf-8')
            CommentBody = CommentList_byte[k]
            NameOfWhoCommentIt_byte = connection.hget(EmailOfWhoCommentIt, 'name')
            NameOfWhoCommentIt = str(NameOfWhoCommentIt_byte, 'utf-8')
            CommentList = AllComment[CounterComment]
            CommentList['name'] = NameOfWhoCommentIt
            CommentList['body'] = str(CommentBody, 'utf-8')
            CounterComment += 1
        tempDictionary['comment'] = AllComment
        tempDictionary['numberOfComment'] = len(CommentList_byte)
        counter += 1

    active = dict(home='', profile='')
    return render(request, 'UserProfile.html',
                  {'UserInfo': UserInfo, 'active': active, 'PostInfo': PostInfo, 'FriendInfo': FriendInfo,
                   'UserInfoDestination': UserInfoDestination})


def BlockUser(request, UserId, DestinationUserId):
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    getUser = connection.hget('user', UserId)
    emailUser = str(getUser, 'utf-8')
    getDestinationUser = connection.hget('user', DestinationUserId)
    emailDestinationUser = str(getDestinationUser, 'utf-8')
    BlocTableNameUser = 'BlockTable' + emailUser
    BlocTableNameDestinationUser = 'BlockTable' + emailDestinationUser
    connection.hset(BlocTableNameDestinationUser, UserId, emailUser)
    connection.hset(BlocTableNameUser, DestinationUserId, emailDestinationUser)
    FollowerTableNameUser = 'FollowerTable' + emailUser
    FollowerTableNameDestinationUser = 'FollowerTable' + emailDestinationUser
    connection.hdel(FollowerTableNameUser, DestinationUserId, emailDestinationUser)
    connection.hdel(FollowerTableNameDestinationUser, UserId, emailUser)
    FollowingTableNameUser = 'FollowingTable' + emailUser
    FollowingTableNameDestinationUser = 'FollowingTable' + DestinationUserId
    connection.hdel(FollowingTableNameUser, DestinationUserId, emailDestinationUser)
    connection.hdel(FollowingTableNameDestinationUser, UserId, emailUser)
    return HttpResponseRedirect('/UserHomePage/' + UserId)


def FollowUser(request, UserId, DestinationUserId):
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    getUser = connection.hget('user', UserId)
    emailUser = str(getUser, 'utf-8')
    getDestinationUser = connection.hget('user', DestinationUserId)
    emailDestinationUser = str(getDestinationUser, 'utf-8')
    FollowingTableNameUser = 'FollowingTable' + emailUser
    FollowerTableNameDestinationUser = 'FollowerTable' + emailDestinationUser
    connection.hset(FollowingTableNameUser, DestinationUserId, emailDestinationUser)
    connection.hset(FollowerTableNameDestinationUser, UserId, emailUser)
    return HttpResponseRedirect('/Profile/' + UserId + '/GotoProfile/' + DestinationUserId)


def UnFollowUser(request, UserId, DestinationUserId):
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    getUser = connection.hget('user', UserId)
    emailUser = str(getUser, 'utf-8')
    getDestinationUser = connection.hget('user', DestinationUserId)
    emailDestinationUser = str(getDestinationUser, 'utf-8')
    FollowingTableNameUser = 'FollowingTable' + emailUser
    FollowerTableNameDestinationUser = 'FollowerTable' + emailDestinationUser
    connection.hdel(FollowingTableNameUser, DestinationUserId, emailDestinationUser)
    connection.hdel(FollowerTableNameDestinationUser, UserId, emailUser)
    return HttpResponseRedirect('/Profile/' + UserId + '/GotoProfile/' + DestinationUserId)
