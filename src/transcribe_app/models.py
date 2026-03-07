# models.py
from django.db import models
import uuid

def upload_to(instance, filename):
    return f"uploads/{instance.created_at.strftime('%Y/%m/%d') if instance.created_at else 'temp'}/{uuid.uuid4().hex}_{filename}"

class Transcript(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=260, blank=True)
    audio_file = models.FileField(upload_to=upload_to, blank=True, null=True)   # NEW
    transcript = models.TextField(blank=True)
    status = models.CharField(max_length=32, default='processing')
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def to_dict(self):
        return {
            'id': str(self.id),
            'filename': self.filename,
            'audio_url': self.audio_file.url if self.audio_file else None,  # NEW
            'transcript': self.transcript,
            'status': self.status,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
        }
