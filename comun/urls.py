from django.urls import path

from . import views

app_name = 'comun'

urlpatterns = [
    path('', views.auditoria, name='auditoria'),
]
