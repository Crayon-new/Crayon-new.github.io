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

  