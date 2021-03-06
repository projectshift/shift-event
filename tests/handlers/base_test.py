from tests.base import BaseTestCase
from nose.plugins.attrib import attr

from shiftevent.handlers import Dummy1
from shiftevent.handlers import NoTypes
from shiftevent.event import Event
from shiftevent import exceptions as x


@attr('event', 'handler', 'base')
class BaseHandlerTest(BaseTestCase):
    """
    Base event handler test. Since it's abstract we're gonna test it through
    a concrete implementations.
    """

    def test_can_accept_custom_context(self):
        """ Handlers can have optional context with dependencies """
        context = dict(dependency='I am a dependency, like some service')
        handler = Dummy1(context=context)
        self.assertEquals(context, handler.context)

    def test_handler_must_define_event_type(self):
        """ Handlers must define event type """
        with self.assertRaises(x.MissingEventType) as cm:
            NoTypes()
        self.assertIn('Event types undefined for handler', str(cm.exception))

    def test_raise_on_handling_unsaved_event(self):
        """ Raise error when trying to handle unsaved event"""
        event = Event(type='DUMMY_EVENT')
        handler = Dummy1()
        with self.assertRaises(x.ProcessingUnsavedEvent) as cm:
            handler.handle_event(event)
        self.assertIn('Unable to handle unsaved event', str(cm.exception))

    def test_raise_error_on_handling_unsupported_event(self):
        """ Raise error on handling unsupported events """
        event = Event(type='UNSUPPORTED', id=123)
        handler = Dummy1()
        with self.assertRaises(x.UnsupportedEventType) as cm:
            handler.handle_event(event)
        self.assertIn('can\'t support events of this type', str(cm.exception))

    def test_raise_on_rolling_back_unsaved_event(self):
        """ Raise error when trying to roll back unsaved event"""
        event = Event(type='DUMMY_EVENT')
        handler = Dummy1()
        with self.assertRaises(x.ProcessingUnsavedEvent) as cm:
            handler.rollback_event(event)
        self.assertIn('Unable to roll back unsaved event', str(cm.exception))

    def test_raise_error_on_rolling_back_usupported_event(self):
        """ Raise error when rolling back unsupported event """
        event = Event(type='UNSUPPORTED', id=123)
        handler = Dummy1()
        with self.assertRaises(x.UnsupportedEventType) as cm:
            handler.rollback_event(event)
        self.assertIn('can\'t support events of this type', str(cm.exception))
