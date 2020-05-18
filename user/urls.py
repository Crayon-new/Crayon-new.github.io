from . import views
from django.urls import path
urlpatterns=[
        path('',views.hello),
        path('regist/',views.regist),
        path('submit',views.submit),
        path('login/',views.login),
         path('login/submit2',views.submit2),
         path('logout',views.logout),
         path('search/',views.ticketQ),
         path('search/buyticket/',views.buy),
         path('usercenter',views.usercenter),
         path('refundticket/',views.refundticket)
]
