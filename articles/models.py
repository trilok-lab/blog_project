from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        def generate_unique_slug(base: str) -> str:
            base_slug = slugify(base)
            candidate = base_slug
            counter = 2
            while Category.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            return candidate

        if not self.slug:
            self.slug = generate_unique_slug(self.name)
        elif self.pk:
            try:
                original = Category.objects.get(pk=self.pk)
                if original.name != self.name:
                    self.slug = generate_unique_slug(self.name)
            except Category.DoesNotExist:
                self.slug = generate_unique_slug(self.name)
        super().save(*args, **kwargs)

    @property
    def permalink(self) -> str:
        return f"/category/{self.slug}"

    def __str__(self) -> str:
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    categories = models.ManyToManyField(Category, related_name='articles', blank=True)
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)  # for homepage slider
    popularity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        def generate_unique_slug(base: str) -> str:
            base_slug = slugify(base)
            candidate = base_slug
            counter = 2
            while Article.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            return candidate

        if not self.slug:
            self.slug = generate_unique_slug(self.title)
        elif self.pk:
            try:
                original = Article.objects.get(pk=self.pk)
                if original.title != self.title:
                    self.slug = generate_unique_slug(self.title)
            except Article.DoesNotExist:
                self.slug = generate_unique_slug(self.title)
        super().save(*args, **kwargs)

    @property
    def permalink(self) -> str:
        return f"/article/{self.slug}"

    def __str__(self) -> str:
        return self.title


