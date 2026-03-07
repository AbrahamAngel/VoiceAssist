from django.urls import path
from transcribe_app.views import home_page, recorder_page, upload_audio, history, download_transcript

urlpatterns = [
    path('', home_page, name='home'),
    path('recorder/', recorder_page, name='recorder'),    
    path('upload-audio/', upload_audio, name='upload_audio'),
	path("history/", history, name="history"),
    path('download/<int:id>/', download_transcript, name='download'),
]
