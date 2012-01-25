from django.db import models
from django.contrib.auth.models import User
from django.db import connections, router, transaction, IntegrityError


KEY_SIZE = 18
SECRET_SIZE = 32

class KeyManager(models.Manager):
    '''Add support for random key/secret generation
    '''
    def generate_random_codes(self):
        key = User.objects.make_random_password(length=KEY_SIZE)
        secret = User.objects.make_random_password(length=SECRET_SIZE)

        while self.filter(key__exact=key, secret__exact=secret).count():
            secret = User.objects.make_random_password(length=SECRET_SIZE)

        return key, secret


class ConsumerManager(KeyManager):
    def create_consumer(self, name, description=None, user=None):
        """
        Shortcut to create a consumer with random key/secret.
        """
        consumer, created = self.get_or_create(name=name)

        if user:
            consumer.user = user

        if description:
            consumer.description = description

        if created:
            consumer.key, consumer.secret = self.generate_random_codes()
            consumer.save()

        return consumer

    _default_consumer = None

class ResourceManager(models.Manager):
    _default_resource = None

    def get_default_resource(self, name):
        """
        Add cache if you use a default resource.
        """
        if not self._default_resource:
            self._default_resource = self.get(name=name)

        return self._default_resource        

class TokenManager(KeyManager):
    def first_or_create(self, **kwargs):
        '''
        Method similar to get_or_create, but get_or_create isn't thread safe.

        As the TokenManager use of get_or_create doesn't use uniqueness feature
        of database it can generate 2 instances in multi-thread environment, which
        leads to MultipleObjectsReturned in further calls.

        It will return first occurance, if not found, create with a new instance.

        This workaround can still create 2 instances, but further calls won't 
        raise MultipleObjectsReturned 

        Most of code here were get from get_or_create Django's implementations.
            basically change .get() to filter()[0]
            and the exception to IndexError
        '''
        assert kwargs, \
                'first_or_create() must be passed at least one keyword argument'
        defaults = kwargs.pop('defaults', {})
        try:
            self._for_write = True
            return self.filter(**kwargs)[0], False
        except IndexError:
            try:
                params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
                params.update(defaults)
                obj = self.model(**params)
                sid = transaction.savepoint(using=self.db)
                obj.save(force_insert=True, using=self.db)
                transaction.savepoint_commit(sid, using=self.db)
                return obj, True
            except IntegrityError, e:
                transaction.savepoint_rollback(sid, using=self.db)
                try:
                    return self.filter(**kwargs)[0], False
                except IndexError:
                    raise self.model.DoesNotExist("%s matching query does not "
                                         "exist." % self.model._meta.object_name)

    def create_token(self, consumer, token_type, timestamp, user=None):
        """
        Shortcut to create a token with random key/secret.
        """
        token, created = self.first_or_create(consumer=consumer, 
                                            token_type=token_type, 
                                            timestamp=timestamp,
                                            user=user)

        if created:
            token.key, token.secret = self.generate_random_codes()
            token.save()

        return token
        
