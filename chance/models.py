from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models



def validate_choice_name(value):
    if value and value.lower() in ('name', 'location', 'starts', 'ends',
        'registration_limit'):
        raise ValidationError(u'%s is a reserved field name, please choose ' \
                'a different one')

class Event(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    starts = models.DateTimeField()
    ends = models.DateTimeField()
    registration_limit = models.PositiveSmallIntegerField(null=True,
            blank=True, default=0)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('chance_event', (), {'pk': self.pk})

    @property
    def registration_open(self):
        return self.registration_limit == 0 or \
            self.registrations.count() < self.registration_limit

class EventFee(models.Model):
    event = models.ForeignKey(Event, related_name='fee_options')
    available = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=255,decimal_places=2)

    def __unicode__(self):
        return u'%s at %s' % (self.name, self.event.name,)

class EventChoice(models.Model):
    event = models.ForeignKey(Event, related_name='choices')
    order = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=32,
            validators=[validate_choice_name])
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    required = models.BooleanField(default=False)
    allow_multiple = models.BooleanField(default=False)

    class Meta:
        ordering = ('order',)
        unique_together = ('name', 'event',)


    def __unicode__(self):
        return '%s at %s' % (self.name, self.event.name,)

class EventChoiceOption(models.Model):
    choice = models.ForeignKey(EventChoice, related_name='options')
    order = models.PositiveIntegerField(default=0)
    display = models.CharField(max_length=128)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return self.display

class Registration(models.Model):
    event = models.ForeignKey(Event, related_name='registrations')
    owner = models.ForeignKey(User, related_name='+', null=True, blank=True)
    attendee_name = models.CharField(max_length=255)
    attendee_email = models.EmailField()
    created = models.DateTimeField(auto_now_add=True, editable=False,
            null=True, blank=True)
    fee_option = models.ForeignKey(EventFee, related_name='+', null=True,
            blank=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ('created',)

    @models.permalink
    def get_absolute_url(self):
        return ('chance_registration', (), {'pk': self.pk, 'event':
            self.event.pk})

    def __unicode__(self):
        return u'Registration for %s by %s' % (self.event.name,
                self.attendee_name,)

class EventChoiceSelection(models.Model):
    registration = models.ForeignKey(Registration, related_name='selections')
    option = models.ForeignKey(EventChoiceOption, related_name='+')


try:
    import reversion
    
    reversion.register(EventChoiceOption)
    reversion.register(EventChoice, follow=['options'])
    reversion.register(EventFee)
    reversion.register(Event, follow=['fee_options', 'choices',
        'choices__options'])

    reversion.register(EventChoiceSelection)
    reversion.register(Registration, follow=['selections'])
except ImportError:
    pass

