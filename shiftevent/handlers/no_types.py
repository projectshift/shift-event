from shiftevent.handlers import BaseHandler


class NoTypes(BaseHandler):
    """
    This handler does not define EVENT_TYPES. It should always fail to
    instantiate. Used for testing
    """

    def handle(self, event):  # pragma: no cover
        """ Handle event """
        pass

    def rollback(self, event):  # pragma: no cover
        """ Rollback event """
        pass


