from django.db import models
from common.models.base import TimestampedModel,UUIDModel
from apps.restaurant.models.restaurant import Restaurant
from apps.core.constants.choices import WeekDays

class OperatingHours(TimestampedModel,UUIDModel):
    
    restaurant = models.ForeignKey(Restaurant,on_delete=models.CASCADE,related_name='operating_hours')
    day_of_week = models.IntegerField(choices=WeekDays.choices,default=WeekDays.MONDAY,db_index=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['restaurant', 'day_of_week']
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_of_week_display()}"
    
class SpecialHours(TimestampedModel,UUIDModel):
    restaurant = models.ForeignKey(Restaurant,on_delete=models.CASCADE,related_name='special_hours')
    date = models.DateField()
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    reason = models.CharField(max_length=200)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.restaurant.name} - {self.date}"