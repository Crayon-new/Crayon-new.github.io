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
         path('1',views.usercenter1),
         path('refundticket/',views.refundticket),
         path('searchStation',views.SeachAllStation),
         path('deleteStation/',views.deleteS),
         path('addstation',views.adds),
         path('2',views.usercenter2),
          path('3',views.usercenter3),
          path('adduser',views.addu),
          path('addT',views.addT),
          path('upT',views.upT)
]
