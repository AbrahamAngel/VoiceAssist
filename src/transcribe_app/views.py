import os
import uuid
import subprocess
import time

from django.shortcuts import render
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import whisper

from transcribe_app.models import Transcript
from transcribe_app.medical_utils import (
    simplify_medical_terms,
    extract_instructions,
    detect_risk
)


MODEL = whisper.load_model("tiny", device="cpu")

def home_page(request):
    return render(request,"transcribe_app/home.html")

def recorder_page(request):
    return render(request, 'transcribe_app/recorder.html')


def _convert_to_wav(input_path, out_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-ar', '16000',
        '-ac', '1',
        '-sample_fmt', 's16',
        out_path
    ]
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


@csrf_exempt
def upload_audio(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'no audio file'}, status=400)

    lang = request.POST.get('language')
    if not lang or lang == 'auto':
        lang = None

    transcript_obj = Transcript.objects.create(
        filename=audio.name,
        status='processing'
    )

    try:
        total_start = time.time()

        saved_name = f"{uuid.uuid4().hex}_{audio.name}"
        transcript_obj.audio_file.save(saved_name, audio, save=True)

        input_path = transcript_obj.audio_file.path
        base, _ = os.path.splitext(input_path)
        wav_path = base + ".wav"

        # ---------- Audio Preprocessing ----------
        preprocess_start = time.time()
        _convert_to_wav(input_path, wav_path)
        preprocess_time = time.time() - preprocess_start

        # ---------- Speech Recognition ----------
        whisper_start = time.time()
        result = MODEL.transcribe(wav_path, language=lang)
        whisper_time = time.time() - whisper_start

        raw_text = result.get('text', '').strip()

        # ---------- Medical NLP ----------
        nlp_start = time.time()
        simplified_text = simplify_medical_terms(raw_text)
        instructions = extract_instructions(simplified_text)
        risk_flag = detect_risk(simplified_text)
        nlp_time = time.time() - nlp_start

        total_time = time.time() - total_start

        print("Audio preprocessing time:", preprocess_time)
        print("Whisper transcription time:", whisper_time)
        print("Medical NLP time:", nlp_time)
        print("Total processing time:", total_time)

        transcript_obj.transcript = simplified_text
        transcript_obj.status = 'done'
        transcript_obj.save()

        if os.path.exists(wav_path):
            os.remove(wav_path)

        return JsonResponse({
            "id": transcript_obj.id,
            "transcript": simplified_text,
            "instructions": instructions,
            "risk": risk_flag,
            "processing_time": round(total_time, 2),
            "status": "done"
        })

    except subprocess.CalledProcessError:
        transcript_obj.status = 'error'
        transcript_obj.error = 'FFmpeg conversion failed'
        transcript_obj.save()
        return JsonResponse({'error': 'FFmpeg failed'}, status=500)

    except Exception as e:
        transcript_obj.status = 'error'
        transcript_obj.error = str(e)
        transcript_obj.save()
        return JsonResponse({'error': str(e)}, status=500)


def history(request):
    items = Transcript.objects.order_by('-created_at')[:50]
    return JsonResponse([t.to_dict() for t in items], safe=False)


def download_transcript(request, id):
    try:
        item = Transcript.objects.get(id=id)
    except Transcript.DoesNotExist:
        raise Http404("Transcript not found")

    if not item.transcript:
        raise Http404("Transcript content missing")

    response = HttpResponse(
        item.transcript,
        content_type="text/plain"
    )
    response["Content-Disposition"] = f'attachment; filename="transcript_{id}.txt"'

    return response