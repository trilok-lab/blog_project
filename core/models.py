from django.db import models


class Theme(models.Model):
    key = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            Theme.objects.exclude(pk=self.pk).update(is_active=False)

    def __str__(self) -> str:
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"


