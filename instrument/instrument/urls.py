from django.contrib import admin
from django.urls import path
from instrument import views
from .views import ImageDetectAPI, InstrumentList, OntologyInfoView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/instrument/', InstrumentList.as_view(), name='instrument_list'),
    path('api/detect/', ImageDetectAPI.as_view(), name='image-detect-api'),
    path('api/detect/<str:one_class_name>/', OntologyInfoView.as_view(), name='ontology_info'),
]

