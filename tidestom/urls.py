"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.urls import path, include
from django.views.generic import TemplateView
from custom_code.templatetags import custom_extras
from .views import (
    SubmitClassificationView, 
    get_subclasses, 
    MyTargetDetailView
)
from custom_code.views import (
    LatestView,
    SnidFormAjaxView,
    NGSFFormAJAXView,
    PreviousSNIDRunsView,
    ToggleTagView,
    TagSearchView,
    ReleaseQueueView,
    ReleaseQueueActionView,
    PublicClassificationsView,
    PublicClassificationsDownloadView,
    StrictTargetUpdateView,
    StrictTargetDeleteView,
    send_to_slack,
)
from myplots.views import (
    target_spectroscopy_partial,
    download_spectrum_ascii,
    download_spectrum_by_specid
)

urlpatterns = [
    path(
        'about/', TemplateView.as_view(template_name='about.html'),
        name='about'
    ),

    path(
        'latest/', LatestView.as_view(),
        name='latest'
    ),

    path(
        'targets/<int:pk>/',
        MyTargetDetailView.as_view(template_name='target_detail.html'),
        name='target_detail'
    ),

    path(
        'targets/<int:target_id>/submit_classification/',
        SubmitClassificationView.as_view(), name='submit_classification'
    ),

    path(
        'api/get_subclasses/', get_subclasses, name='get_subclasses'
    ),
    path(
        'targets/<int:pk>/update/',
        StrictTargetUpdateView.as_view(),
        name='target_update'
    ),
    path(
        'targets/<int:pk>/delete/',
        StrictTargetDeleteView.as_view(),
        name='delete_target'
    ),
    path(
        '', include('tom_common.urls')
    ),
    path(
        'api/classifications/',
         custom_extras.classification_data,
         name='classification_data'
    ),
    path(
        'api/average-spectrum/<str:sn_type>/', 
        custom_extras.average_spectrum_by_type, 
        name='average_spectrum_by_type'
    ),
    path(
        "snid/run/", SnidFormAjaxView.as_view(), name="snid-run"
    ),
    path(
        "ngsf/run/", NGSFFormAJAXView.as_view(), name="ngsf-run"
    ),
    path(
        "target_spectroscopy/<int:target_id>/", target_spectroscopy_partial,
        name="target_spectroscopy"
        ),
    path(
        "download_spectrum/<int:target_id>/", download_spectrum_ascii,
        name="download_spectrum",
    ),
    path(
        "download_spectrum_by_specid/<int:tides_specid>/", download_spectrum_by_specid,
        name="download_spectrum_by_specid",
    ),
    path(
        "api/previous_snid_runs/", PreviousSNIDRunsView.as_view(),
        name="previous_snid_runs"
    ),
    path('targets/<int:target_id>/tags/toggle/<int:tag_id>/', ToggleTagView.as_view(), name='toggle_tag'),
    path('tags/search/', TagSearchView.as_view(), name='tags_search'),
    path(
        'release-queue/',
        ReleaseQueueView.as_view(),
        name='release_queue',
    ),
    path(
        'release-queue/apply/',
        ReleaseQueueActionView.as_view(),
        name='release_queue_apply',
    ),
    path(
        'public/classifications/',
        PublicClassificationsView.as_view(),
        name='public_classifications',
    ),
    path(
        'public/classifications/download/',
        PublicClassificationsDownloadView.as_view(),
        name='public_classifications_download',
    ),

    path(
        "send-to-slack/",
        send_to_slack,
        name="send_to_slack"
),
]
