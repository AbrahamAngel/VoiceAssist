from django.urls import path
from transcribe_app.views import recorder_page, upload_audio, history, download_transcript

urlpatterns = [
    path('', recorder_page, name='recorder'),    
    path('upload-audio/', upload_audio, name='upload_audio'),
	path("history/", history, name="history"),
	path("download/<str:id>/", download_transcript, name="download"),

]
