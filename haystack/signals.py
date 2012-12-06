from django.db import models
from haystack.exceptions import NotHandled


class BaseSignalProcessor(object):
    """
    A convenient way to attach Haystack to Django's signals & cause things to
    index.

    By default, does nothing with signals but provides underlying functionality.
    """
    def __init__(self, connections, connection_router):
        self.connections = connections
        self.connection_router = connection_router
        self.setup()

    def setup(self):
        # Do nothing.
        pass

    def teardown(self):
        # Do nothing.
        pass

    def handle_save(self, sending_object):
        using_backends = self.connection_router.for_write(sending_object)

        for using in using_backends:
            try:
                index = self.connections[using].get_unified_index().get_index(sending_object.__class__)
                index.update_object(sending_object, using=using)
            except NotHandled:
                # FIXME: Maybe log it or let the exception bubble?
                pass

    def handle_delete(self, sending_object):
        using_backends = self.connection_router.for_write(sending_object)

        for using in using_backends:
            try:
                index = self.connections[using].get_unified_index().get_index(sending_object.__class__)
                index.remove_object(sending_object, using=using)
            except NotHandled:
                # FIXME: Maybe log it or let the exception bubble?
                pass


class RealtimeSignalProcessor(BaseSignalProcessor):
    """
    Allows for observing when saves/deletes fire & automatically updates the
    search engine appropriately.
    """
    def setup(self):
        # Naive.
        models.signals.post_save.connect(self.handle_save, sender=models.Model)
        models.signals.post_delete.connect(self.handle_delete, sender=models.Model)
        # Efficient would be going through all backends & collecting all models
        # being used, then hooking up signals only for those.

    def teardown(self):
        # Naive.
        models.signals.post_save.disconnect(self.handle_save, sender=models.Model)
        models.signals.post_delete.disconnect(self.handle_delete, sender=models.Model)
        # Efficient would be going through all backends & collecting all models
        # being used, then disconnecting signals only for those.
