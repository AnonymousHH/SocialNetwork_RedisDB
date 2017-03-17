from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.enterPage, name="enterPage"),
    url(r'^Login$', views.Login, name="Login"),
    url(r'^Register$', views.Register, name="Register"),
    url(r'^UserHomePage/(\d+)$', views.UserHomePage, name="Home"),
]
