from inspect import isclass
from shiftevent.event import Event, EventSchema
from shiftevent import exceptions as x
from shiftevent.default_handlers import default_handlers
from shiftevent.handlers import BaseHandler


class EventService:
    """
    Event service
    Responsible for handling events
    """

    # database instance
    db = None

    # event handlers
    handlers = None

    # context for handlers
    handler_context = None

    def __init__(self, db, handlers=None, handler_context=None):
        """
        Initialize event service
        Accepts a database instance to operate on events and projections.
        :param db: shiftevent.db.Db, database instance
        :param handlers: dict, optional handlers configuration
        :param context: dict, context to pass to handlers
        """
        self.db = db
        self.handlers = handlers if handlers else default_handlers
        self.handler_context = handler_context

    def event(
        self,
        type,
        author,
        object_id=None,
        payload=None,
        payload_rollback=None):
        """
        Persist an event
        Creates a new event object, validates it and saves to the database.
        May throw a validation exception if some event data is invalid.

        :param type: str, event type
        :param author:  str, author id in external system
        :param object_id: str, an id of the object being affected
        :param payload: dict, event payload
        :param payload_rollback: dict, payload to roll back an event
        :return: shiftevent.event.Event
        """
        # create
        event = Event(
            type=type,
            author=author,
            object_id=object_id,
            payload=payload,
            payload_rollback=payload_rollback
        )

        event = self.save_event(event)
        return event

    def emit(self, event):
        """
        Emit event
        Initialises every handler in the chain for the event and sequentially
        executes each one.
        :param event: shiftevent.events.event.Event
        :return:
        """
        if event.type not in self.handlers:
            raise x.EventError('No handlers for event {}'.format(event.type))

        # trigger handlers
        handlers = self.handlers[event.type]
        chain = []
        for handler in handlers:
            if not isclass(handler):
                msg = 'Handler {} for {} has to be a class, got [{}]'
                raise x.HandlerInstantiationError(msg.format(
                    handler,
                    event.type,
                    type(handler)
                ))

            handler = handler(context=self.handler_context)
            if not isinstance(handler, BaseHandler):
                msg = 'Handler implementations must extend BaseHandler'
                raise x.HandlerInstantiationError(msg)

            # append to chain if valid
            chain.append(handler)

        # all valid? run chain
        ran = []
        for handler in chain:
            try:
                ran.append(handler)
                handled = handler.handle_event(event)
                if handled:
                    event = handled
                else:
                    break  # skip next handler
            except Exception as handler_exception:

                # first, reverse all handlers that ran
                for handler in ran:
                    handled = handler.rollback_event(event)
                    if handled:
                        event = handled

                # drop event from the store
                events = self.db.tables['events']
                with self.db.engine.begin() as conn:
                    conn.execute(events.delete().where(
                        events.c.id == event.id
                    ))

                # re-raise the exception
                raise handler_exception

        # return event at the end
        return event

    def save_event(self, event):
        """
        Save event
        Validates and persist event object. This should only get run
        to persist and event after all the handlers ran.

        :param event: shiftevent.event.Event
        :return: shiftevent.event.Event
        """
        if event.type not in self.handlers:
            raise x.EventError('No handlers for event {}'.format(event.type))

        # validate
        schema = EventSchema()
        ok = schema.process(event)
        if not ok:
            raise x.InvalidEvent(validation_errors=ok.get_messages())

        # and save
        events = self.db.tables['events']
        with self.db.engine.begin() as conn:
            data = event.to_db()
            del data['id']
            result = conn.execute(events.insert(), **data)
            event.id = result.inserted_primary_key[0]

        return event

    def get_event(self, id):
        """
        Get event
        Returns event found by unique id.
        :param id: int, event id
        :return: shiftevent.event.Event
        """
        event = None
        events = self.db.tables['events']
        with self.db.engine.begin() as conn:
            select = events.select().where(events.c.id == id)
            data = conn.execute(select).fetchone()
            if data:
                event = Event(**data)
        return event








