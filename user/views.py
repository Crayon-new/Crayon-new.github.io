from django.http import HttpResponse
import random
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django import forms
from datetime import date
from django.core.mail import send_mail
from django.template import loader,Context
from user.models import Users
from user.model import User, Train, Ticket, Station, Order, ModelBase
# Create your views here.
from .form import UserForm,passform,loginiform,searchT,searchS,stationform,ticketform,upTform
from user.searchTicket import Manager,pPassenger
m = Manager('postgresql://checker:123456@127.0.0.1:5432/test')
ModelBase.metadata.create_all(m.engine)
count1 = 0
i = 0
username ="" #正在注册个体
password = "" #正在注册个体密码
email = ""#正在注册个体邮箱
loginUser = "" #正在使用网站的个体

#登录注册注销操作
def hello(request):
     return render(request,'index.html')
     
def login(request):
    return render(request,'login.html')

def submit2(request):
 global loginUser
 if request.method=='POST':
    log = loginiform(request.POST)
    if log.is_valid():
     username2 = log.cleaned_data['loguser']
     password2 =  log.cleaned_data['logpass']
     try:
      if not request.COOKIES.get('username','')=="":
           return HttpResponse("不可重复登录")
      res = m.validate(username2, password2)
      if  res!=False:
          if res.user_type == 'SuperUser':
              loginUser = username2
              response = HttpResponse("欢迎,尊敬的管理员"+" "+loginUser+" !  返回点击个人中心即可进入管理页面")
          elif res.user_type=='Passenger':
              loginUser = username2
              response = HttpResponse("欢迎"+" "+loginUser)
          #将username2写入浏览器cookie,失效时间为3600
          response.set_cookie('username',username2,3600)
          response.set_cookie('password',password2,3600)
          return response
          return HttpResponse("欢迎!"+" "+request.COOKIES.get('username',''))
      else:
          return HttpResponse("密码错误或用户名不存在，请返回重新输入用户名密码！")
     except:
          return HttpResponse("错误")



def logout(request):
   if not request.COOKIES.get('username','')=="":
    response = HttpResponse('logout !!'+request.COOKIES.get('username',''))
    #清理cookie里保存username
    response.delete_cookie('username')
   else:
       response = HttpResponse("无用户登录")
   return response
 
def regist(request):
    return render(request,'regist.html')



def submit(request):
    global count1,i,username,password,email
    if request.method == 'POST':
        userform = UserForm(request.POST)
        if userform.is_valid() and count1==0:
            count1+=1
            i = random.randint(100000,999999)
            username = userform.cleaned_data['username']
            password = userform.cleaned_data['password']
            email = userform.cleaned_data['email']
            send_mail('Subject here', '您的注册验证码为: '+str(i), '1349159541@qq.com',
             [email], fail_silently=False)
            return HttpResponse("发送成功，请返回验证")
        else:
         userform2 = passform(request.POST)
         if userform2.is_valid():
             passi = userform2.cleaned_data['pas']
             if passi==str(i) :
                 try:
                   if  m.createUser(pPassenger.create(username, password, email)):
                        count1=0
                        return HttpResponse("注册成功")
                   else:
                        return HttpResponse("邮箱或用户已被注册")
                 except:
                    return HttpResponse("邮箱或用户已被注册")
             else:
                 count1 = 0
                 return HttpResponse("验证码错误 请返回并重新发送验证码")
         else:
            coutn1 = 0
            return HttpResponse("请填写完整后提交")


# 查询火车票操作
def ticketQ(request):
  if request.method == 'POST':
      Sform = searchT(request.POST)
      if Sform.is_valid():
       fromwhere = Sform.cleaned_data['From']
       towhere = Sform.cleaned_data['To']
       date = Sform.cleaned_data['Date']
    #    if date.today()>date:
    #        return HttpResponse('您选择的日期不在预售期范围内')
       tlist = m.search(date,fromwhere,towhere)
       tlist = Paginator(tlist, 5) # Show 25 contacts per page
       page = request.GET.get('page')
       try:
        tlist = tlist.page(page)
       except PageNotAnInteger:
        # If page is not an integer, deliver first page.
         tlist = tlist.page(1)
       except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
         tlist = tlist.page(tlist.num_pages)
       return render(request,'search.html',
       {'tlist':tlist,
       'fromwhere':fromwhere,
       'towhere':towhere,
       'date':date})
      else:
          return HttpResponse(loginUser)
  else:
    date = request.GET.get('date')
    fromwhere = request.GET.get('fromwhere')
    towhere = request.GET.get('towhere')
    print(date)
    print(fromwhere)
    print(towhere)
    page = request.GET.get('page')
    print(page)
    tlist = m.search(date,fromwhere,towhere)
    tlist= Paginator(tlist, 5) # Show 25 contacts per page

    try:
        tlist = tlist.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tlist = tlist.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        tlist = tlist.page(tlist.num_pages)
    return render(request,'search.html',
       {'tlist':tlist,
       'fromwhere':fromwhere,
       'towhere':towhere,
       'date':date})



def buy(request):
    if request.COOKIES.get('username','')=="":
        return HttpResponse('请先登录')
    else:
     if request.method=='GET':
          list1 = request.GET.get('tid')
          print(list1)
          res = m.reserve(list1,request.COOKIES.get('username',''))
          if res==1:
            return HttpResponse("订票成功")
          elif res==0:
              return HttpResponse("余票不足，购票失败")
          elif res ==-1:
              return HttpResponse("请先登录")
          else:
              return HttpResponse("您已购买改区间段的其他车票，请勿重复购买")
                
     else:
         return HttpResponse('请求错误！')



def usercenter1(request):
     if request.COOKIES.get('username','')=="":
        return HttpResponse('请先登录')
     else:
      res = m.checkUserType(request.COOKIES.get('username',''))
      if res !=None: 
       if res.user_type=='Passenger':
        tlist = m.checkOrders(request.COOKIES.get('username',''))
        return render(request,'usercenter.html',{'tlist':tlist})
       elif res.user_type=='SuperUser':
        return render(request,'managers1.html',{'manager':request.COOKIES.get('username','')})
      else:
          return HttpResponse('错误')

def usercenter2(request):
 return render(request,'managers2.html',{'manager':request.COOKIES.get('username','')})

def usercenter3(request):
 return render(request,'managers3.html',{'manager':request.COOKIES.get('username','')})


def refundticket(request):
    if request.method=='GET':
          list1 = request.GET.get('tid')
          res = m.refund(request.COOKIES.get('username',''),list1)
          if res:
               return HttpResponse("退票成功")
          else:
              return HttpResponse('该订单已被处理')
    else:
         return HttpResponse('请求错误！')

def SeachAllStation(request):
  if request.method=="POST":
        Sform = searchS(request.POST)
        if Sform.is_valid():
            train_name = Sform.cleaned_data['train_name']
            Slist = m.searchStationsOf(train_name)
            Slist = Paginator(Slist, 5) # Show 25 contacts per page
            page = request.GET.get('page')
            try:
              Slist = Slist.page(page)
            except PageNotAnInteger:
            # If page is not an integer, deliver first page.
               Slist = Slist.page(1)
            except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
               Slist =Slist.page(Slist.num_pages)
            return render(request,'managers2.html',
            {'Slist':Slist,
            'train_name':train_name})
        else:
          return HttpResponse(loginUser)
  else:
    tarin_name = request.get('train_name')
    page = request.GET.get('page')
    print(page)
    Slist = m.search(train_name)
    Slist= Paginator(Slist, 5) # Show 25 contacts per page

    try:
        Slist = Slist.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        Slist = Slist.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
       Slist =Slist.page(Slist.num_pages)
    return render(request,'managers2.html',
       {'Sist':Slist,
      'train_name':train_name})

def deleteS(request):
    if request.COOKIES.get('username','')=="":
        return HttpResponse('请先登录')
    else:
     if request.method=='GET':
          station_id= request.GET.get('tid')
          train_name = request.GET.get('train_name')
          print(station_id)
          print(train_name)
          res = m.removeStationFrom(station_id,train_name)
          if res:
            return HttpResponse("删除车站成功")
          else:
              return HttpResponse("操作失败")
     else:
         return HttpResponse('请求错误！')

def adds(request):
     if request.method=="POST":
        Sform = stationform(request.POST)
        if Sform.is_valid():
           station_code = Sform.cleaned_data['station_code']
           station_name= Sform.cleaned_data['station_name']
           city_name= Sform.cleaned_data['city_name']
           res = m.createStation(station_code,station_name,city_name)
           if res==1:
               return HttpResponse("增加车站成功")
           else:
               return HttpResponse("增加车站失败")
        else:
             return HttpResponse("请正确填写内容")
     else:
         return HttpResponse("错误")

def addu(request):
    if request.method=="POST":
        Uform = UserForm(request.POST)
        if Uform.is_valid():
           username= Uform.cleaned_data['username']
           password= Uform.cleaned_data['password']
           email= Uform.cleaned_data['email']
           res =  m.createUser(pPassenger.create(username, password, email))
           if res:
               return HttpResponse("增加用户成功")
           else:
               return HttpResponse("增加用户失败")
        else:
             return HttpResponse("请正确填写内容")
    else:
         return HttpResponse("错误")


def addT(request):
     if request.method=="POST":
         Tform = ticketform(request.POST)
         if Tform.is_valid():
               Date =  Tform.cleaned_data['Date']
               Start =  Tform.cleaned_data['Start']
               End =   Tform.cleaned_data['End']
               From =Tform.cleaned_data['From']
               To =  Tform.cleaned_data['To']
               depart = Tform.cleaned_data['depart']
               arrive = Tform.cleaned_data['arrive']
               diff =Tform.cleaned_data['diff']
               train_id=Tform.cleaned_data['train_id']
               ticketnum = Tform.cleaned_data['ticketnum']
               seat_type =  Tform.cleaned_data['seat_type']
               price = Tform.cleaned_data['price']
               res = m.addTicketToTrain(Date,Start,End,From,To,depart,arrive,
               diff,train_id,ticketnum,seat_type,price)
               if res==1:
                return HttpResponse("增加车票成功")
               else:
                 return HttpResponse("增车票失败")
         else:
             return HttpResponse("请正确填写内容")
     else:
         return HttpResponse("错误")
    
def upT(request):
     if request.method=="POST":
         Tform = upTform (request.POST)
         if Tform.is_valid():
             ticket_id =  Tform.cleaned_data['ticket_id']
             price =  Tform.cleaned_data['price']
             res = m.updateTicketPrice(ticket_id,price)
             if res ==1:
                  return HttpResponse("更新票价成功")
             else:
                 return HttpResponse("更新票价失败")
         else:
             return HttpResponse("请正确填写内容")
     else:
         return HttpResponse("错误")
