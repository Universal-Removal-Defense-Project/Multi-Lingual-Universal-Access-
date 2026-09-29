from django.urls import path

from . import views

urlpatterns = [
    path('asylum-intake/', views.intake_form, name='intake_form'),
    path('intake-success/', views.intake_success, name='intake_success'),
    # Unlinked until attorney sign-off (#41); reachable by direct URL only.
    path('intake-form/', views.application_start, name='application_start'),
    path('intake-form/<int:step>/', views.application_step, name='application_step'),
]
