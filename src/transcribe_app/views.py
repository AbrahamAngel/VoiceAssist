import os
import uuid
import subprocess
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import FileResponse, Http404

import whisper

from transcribe_app.models import Transcript

MODEL = whisper.load_model("tiny", device="cpu")

def recorder_page(request):
    return render(request, 'transcribe_app/recorder.html')

def _convert_to_wav(input_path, out_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-ar', '16000', '-ac', '1', '-sample_fmt', 's16',
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@csrf_exempt
def upload_audio(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'no audio file'}, status=400)

    lang = request.POST.get('language', None)
    if lang == 'auto' or not lang:
        lang = None

    # Create DB record early
    transcript_obj = Transcript.objects.create(
        filename=audio.name,
        status='processing'
    )

    try:
        # Save uploaded file to the model's FileField (Django storage)
        # We give a unique name to avoid conflicts
        saved_name = f"{uuid.uuid4().hex}_{audio.name}"
        # The .save() method writes file to MEDIA_ROOT via storage backend
        transcript_obj.audio_file.save(saved_name, audio, save=True)

        # Now we have a file saved in storage; get its filesystem path
        # NOTE: .path works only for local filesystem storage (default).
        input_path = transcript_obj.audio_file.path

        # Build path for converted wav - in same folder
        base, _ = os.path.splitext(input_path)
        wav_path = base + ".wav"

        # Convert using ffmpeg
        _convert_to_wav(input_path, wav_path)

        # Transcribe
        result = MODEL.transcribe(wav_path, language=lang)
        text = result.get('text', '').strip()

        # Save transcript and update status
        transcript_obj.transcript = text
        transcript_obj.status = 'done'
        transcript_obj.save()

        # Remove only the temp wav if you don't want to keep it
        try:
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except OSError:
            pass

        return JsonResponse(transcript_obj.to_dict())

    except subprocess.CalledProcessError:
        transcript_obj.status = 'error'
        transcript_obj.error = 'ffmpeg conversion failed — is ffmpeg installed?'
        transcript_obj.save()
        return JsonResponse(transcript_obj.to_dict(), status=500)

    except Exception as e:
        transcript_obj.status = 'error'
        transcript_obj.error = str(e)
        transcript_obj.save()
        return JsonResponse(transcript_obj.to_dict(), status=500)

def history(request):
    items = Transcript.objects.all()[:50] 
    return JsonResponse([t.to_dict() for t in items], safe=False)


def download_transcript(request, id):
    try:
        item = Transcript.objects.get(id=id)
    except Transcript.DoesNotExist:
        raise Http404("Transcript not found")

    path = os.path.join(settings.MEDIA_ROOT, item.filename or "audio.webm")
    if not os.path.exists(path):
        raise Http404("Audio file missing")

    return FileResponse(open(path, 'rb'), as_attachment=True, filename=item.filename)