from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4


class GazetteSubscription(Base, TimestampMixin, ContentMixin):
    """ A supscription to a (filtered) collection of published notices. """

    __tablename__ = 'gazette_subscriptions'

    #: The ID of the subscription.
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The email of the subscriber.
    email = Column(Text, nullable=False)

    #: The locale of the subscriber.
    locale = Column(Text, nullable=False)

    #: True if the email of the subscriber has been validated.
    validated = Column(Boolean, nullable=False)

    #: The last time, the subscription was delivered.
    last_sent = Column(UTCDateTime, nullable=True)

    #: An term to search (optional).
    term = meta_property('term')

    #: The order of the results (optional).
    order = meta_property('order')

    #: The direction of the order of the results (optional).
    direction = meta_property('direction')

    #: The categories to cover (optional).
    categories = meta_property('categories')

    #: The organizations to cover (optional).
    organizations = meta_property('organizations')
