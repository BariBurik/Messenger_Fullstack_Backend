"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from strawberry.django.views import AsyncGraphQLView

from messenger.graphene import graphene_schema
from messenger.middlewares import StrawberryAuthMiddleware
from messenger.strawberry import schema as strawberry_schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path("graphql/graphene/", GraphQLView.as_view(graphiql=True, schema=graphene_schema)),
    path("graphql/strawberry/", StrawberryAuthMiddleware(AsyncGraphQLView.as_view(schema=strawberry_schema))),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
