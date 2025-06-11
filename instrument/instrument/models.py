from django.db import models


class Instrument(models.Model):

    name = models.CharField(max_length=100)

    description = models.TextField()

class Img_predictions(models.Model):
    image = models.ImageField(upload_to='images/')
    prediction = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.image.name