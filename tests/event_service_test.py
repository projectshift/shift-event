from tests.base import BaseTestCase
from nose.plugins.attrib import attr
from unittest.mock import MagicMock

from pprint import pprint as pp
from inspect import isclass
from shiftevent import exceptions as x
from shiftevent.event_service import EventService
from shiftevent.event import Event
from shiftevent.handlers import Dummy1
from shiftevent.handlers import Dummy2
from shiftevent.handlers import Dummy3
from shiftevent.handlers import Dummy4


@attr('event', 'service')
class EventServiceTest(BaseTestCase):

    def test_create_event_service(self):
        """ Creating event service"""
        service = EventService(db=self.db)
        self.assertIsInstance(service, EventService)

    def test_raise_validation_errors_when_creating_invalid_event(self):
        """ Raise validation exception when creating event from bad data"""
        service = EventService(db=self.db)
        try:
            service.event(
                type='DUMMY_EVENT',
                object_id=None,
                author=456,
                payload={'what': 'IS THIS'}
            )
        except x.InvalidEvent as err:
            self.assertIn('object_id', err.validation_errors)

    def test_create_event(self):
        """ Creating an event """
        service = EventService(db=self.db)

        payload = {'what': 'IS THIS'}
        payload_rollback = {'rollback': 'data'}

        event = service.event(
            type='DUMMY_EVENT',
            object_id=123,
            author=456,
            payload=payload,
            payload_rollback=payload_rollback,
        )
        self.assertEquals(1, event.id)
        self.assertEquals(payload, event.payload)
        self.assertEquals(payload_rollback, event.payload_rollback)

    def test_raise_on_missing_handler_when_creating_an_event(self):
        """ Raise exception on missing event handler when creating an event"""
        service = EventService(db=self.db)
        with self.assertRaises(x.EventError):
            service.event(
                type='UNKNOWN_EVENT_TYPE',
                object_id=123,
                author=456,
                payload={'what': 'IS THIS'}
            )

    def test_save_an_event(self):
        """ Saving an event """
        event = Event(
            type='DUMMY_EVENT',
            object_id=123,
            author=123,
            payload={'body': 'I am the payload 😂'},
            payload_rollback={'body': 'I am rollback payload 😂'},
        )

        service = EventService(db=self.db)
        service.save_event(event)
        self.assertEquals(1, event.id)

    def test_raise_exception_on_saving_event_with_no_handlers(self):
        """ Raise when saving event with no handlers """
        event = Event(
            type='UNKNOWN_EVENT_TYPE',
            object_id=123,
            author=456,
            payload={'what': 'IS THIS'}
        )
        with self.assertRaises(x.EventError):
            service = EventService(db=self.db)
            service.save_event(event)

    def test_raise_exception_on_saving_invalid_event(self):
        """ Raise exception when saving invalid event """
        event = Event(
            type='DUMMY_EVENT',
            object_id=123,
            payload={'body': 'I am the payload 😂'},
            payload_rollback={'body': 'I am rollback payload 😂'},
        )
        with self.assertRaises(x.InvalidEvent) as cm:
            service = EventService(db=self.db)
            service.save_event(event)
        self.assertIn('author', cm.exception.validation_errors)

    def test_get_event_by_id(self):
        """ Getting event by id"""
        service = EventService(db=self.db)
        event = service.event(
            type='DUMMY_EVENT',
            object_id=123,
            author=456,
            payload={'what': 'IS THIS'},
        )

        id = event.id
        event = service.get_event(id)
        self.assertIsInstance(event, Event)
        self.assertEquals(id, event.id)

    def test_instantiate_handler(self):
        """ Instantiating handler """
        handler_definitions = dict(DUMMY_EVENT=[Dummy1])
        service = EventService(db=self.db, handlers=handler_definitions)
        event = Event(type='DUMMY_EVENT', id=123, payload=dict(some='payload'))
        event = service.emit(event)
        self.assertIn('dummy_handler1', event.payload)

    def test_raise_when_handler_not_defined_as_a_class(self):
        """ Raise an error when handler is not a class """
        handler_definitions = dict(DUMMY_EVENT=[Dummy1()])
        service = EventService(db=self.db, handlers=handler_definitions)
        event = Event(type='DUMMY_EVENT', id=123, payload=dict(some='payload'))
        with self.assertRaises(x.HandlerInstantiationError) as cm:
            service.emit(event)
        self.assertIn('has to be a class, got', str(cm.exception))

    def test_raise_when_handler_doesnt_inherit_from_base(self):
        """ Raise error when handler does not extend from base """
        class Handler:
            def __init__(self, *args, **kwargs):
                pass

            def handle(self, *args, **kwargs):
                pass

        handler_definitions = dict(DUMMY_EVENT=[Handler])
        service = EventService(db=self.db, handlers=handler_definitions)
        event = Event(type='DUMMY_EVENT', id=123, payload=dict(some='payload'))
        with self.assertRaises(x.HandlerInstantiationError) as cm:
            service.emit(event)
        self.assertIn(
            'Handler implementations must extend BaseHandler',
            str(cm.exception)
        )

    def test_raise_on_missing_handler_when_emitting_an_event(self):
        """ Raise exception on missing event handler when emitting an event"""
        service = EventService(db=self.db)
        event = Event(
            type='UNKNOWN_EVENT_TYPE',
            object_id=123,
            author=456,
            payload={'what': 'IS THIS'}
        )
        with self.assertRaises(x.EventError):
            service.emit(event)

    def test_can_emit_an_event_and_run_handler_sequence(self):
        """ Emitting an event and running handler sequence"""
        service = EventService(db=self.db)
        event = service.event(
            type='DUMMY_EVENT',
            object_id=123,
            author=456,
            payload={'what': 'IS THIS'}
        )

        processed = service.emit(event)
        self.assertIn('dummy_handler1', processed.payload)
        self.assertIn('dummy_handler2', processed.payload)

    def test_handlers_instantiated_with_context_if_set(self):
        """ Event service passes dependency context to handlers if configured"""
        handler = Dummy2
        handler.__init__ = MagicMock(return_value=None)

        context = dict(dependency='Some dependency')
        service = EventService(db=self.db, handler_context=context)
        service.handlers['DUMMY_EVENT'].append(handler)

        event = service.event(
            type='DUMMY_EVENT',
            object_id=123,
            author=456,
            payload={'what': 'IS THIS'}
        )

        service.emit(event)
        handler.__init__.assert_called_with(context=context)

    def test_rollback_handlers_on_exception(self):
        """ Rollback applied handlers on handler exceptions """

        # create event
        service = EventService(db=self.db)
        event = service.event(
            type='DUMMY_EVENT',
            object_id=123,
            author=456,
            payload={'what': 'IS THIS'}
        )

        # create handlers
        handler1 = Dummy1
        handler1.handle = MagicMock(return_value=event)
        handler1.rollback = MagicMock(return_value=event)

        handler2 = Dummy2
        handler2.handle = MagicMock(return_value=event)
        handler2.rollback = MagicMock(return_value=event)

        handler3 = Dummy3
        handler3.handle = MagicMock(side_effect=Exception('Handler exception'))
        handler3.rollback = MagicMock(return_value=event)

        handler4 = Dummy4
        handler4.handle = MagicMock(return_value=event)
        handler4.rollback = MagicMock(return_value=event)

        # attach to service
        service.handlers = dict(
            # dummy handlers
            DUMMY_EVENT=[
                handler1,
                handler2,
                handler3,
                handler4,
            ],
        )

        # assert raised
        with self.assertRaises(Exception) as cm:
            service.emit(event)
        self.assertIn('Handler exception', str(cm.exception))

        # assert first handlers ran
        handler1.handle.assert_called_with(event)
        handler2.handle.assert_called_with(event)
        handler3.handle.assert_called_with(event)

        # assert handlers after the exception weren't called
        handler4.handle.assert_not_called()

        # assert handlers before exception rolled back
        handler1.rollback.assert_called_with(event)
        handler2.rollback.assert_called_with(event)
        handler3.rollback.assert_called_with(event)

        # assert handlers after the exception not called
        handler4.rollback.assert_not_called()

        # assert event dropped from the store
        self.assertIsNone(service.get_event(event.id))








