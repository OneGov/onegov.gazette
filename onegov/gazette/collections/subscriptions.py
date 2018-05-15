from onegov.core.collection import GenericCollection
from onegov.gazette.models import GazetteSubscription


class SubscriptionCollection(GenericCollection):

    @property
    def model_class(self):
        return GazetteSubscription

    def by_email(self, email):
        return self.query().filter(GazetteSubscription.email == email).first()
