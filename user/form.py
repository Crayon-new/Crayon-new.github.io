from django import forms

class UserForm(forms.Form):
    username = forms.CharField(label='用户名',max_length=50)
    password = forms.CharField(label='密码',widget=forms.PasswordInput())
    email = forms.EmailField(label='邮箱')
class passform(forms.Form):
    pas = forms.CharField(label='验证码')
class loginiform(forms.Form):
    loguser = forms.CharField(label='用户名',max_length=50)
    logpass = forms.CharField(label='密码',widget=forms.PasswordInput())
class searchT(forms.Form):
    From =  forms.CharField(label='出发地',max_length=50)
    To =   forms.CharField(label='到达地',max_length=50)
    Date = forms.DateField()
class searchS(forms.Form):
    train_name=forms.CharField(label='车次',max_length=50)
class stationform(forms.Form):
    station_code=  forms.CharField(label='站编号',max_length=50)
    station_name = forms.CharField(label='站名',max_length=50)
    city_name = forms.CharField(label='城市名',max_length=50)

class ticketform(forms.Form):
    Date = forms.DateField()
    Start =  forms.CharField(label='始发地',max_length=50)
    End =   forms.CharField(label='终点地',max_length=50)
    From =  forms.CharField(label='出发地',max_length=50)
    To =   forms.CharField(label='到达地',max_length=50)
    depart = forms.TimeField()
    arrive = forms.TimeField()
    diff = forms.IntegerField()
    train_id=forms.IntegerField()
    ticketnum =forms.IntegerField()
    seat_type =forms.CharField(label='座位类型',max_length=50)
    price = forms.IntegerField()

class upTform(forms.Form):
    ticket_id =forms.IntegerField()
    price = forms.IntegerField()