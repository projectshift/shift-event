from shiftevent.handlers import BaseHandler


class Dummy4(BaseHandler):
    """
    Dummy handler 4
    This is mostly used for testing. The side effect it produces is modifying
    the event payload. Be careful, in reality you should never modify an event
    as they are immutable.
    """

    EVENT_TYPES = (
        'DUMMY_EVENT',
    )

    def handle(self, event):
        """ Handle event """
        payload = event.payload
        payload['dummy_handler4'] = 'processed'
        event.payload = payload
        return event

    def rollback(self, event):
        """ Rollback event """
        payload = event.payload
        if 'dummy_handler4' in payload:
            del payload['dummy_handler4']

        event.payload = payload
        return event


