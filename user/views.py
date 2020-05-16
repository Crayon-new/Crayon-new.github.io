from django.http import HttpResponse
import random
from django.shortcuts import render
from django import forms
from django.core.mail import send_mail
from django.template import loader,Context
from user.models import Users
from user.model import Ticket
# Create your views here.
from .form import UserForm,passform,loginiform,searchT

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
      user = Users.objects.get(username=username2)
      if user.password==password2:
          loginUser = username2
          response = HttpResponse("欢迎!"+" "+loginUser)
                #将username2写入浏览器cookie,失效时间为3600
          response.set_cookie('username',username2,3600)
          return response
          return HttpResponse("欢迎!"+" "+request.COOKIES.get('username',''))
      else:
          return HttpResponse("密码错误，请返回重新输入密码！")
     except:
          return HttpResponse("用户名不存在")
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
                   Users.objects.create(username=username,password=password,email=email)
                 except:
                    return HttpResponse("邮箱或用户已被注册")
                 count1 = 0
                 return HttpResponse("注册成功")
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
    
       tlist=Ticket.query(fromwhere,towhere,date)
       return render(request,'search.html',{'tlist':tlist})
      else:
          return HttpResponse(loginUser)
