from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.gazette.models import Category


class CategoryCollection(AdjacencyListCollection):
    """ Manage a list of categories.

    The list is ordered by the title, unless the ordering is set manually
    (which should never occure in our case).

    """

    __listclass__ = Category

    def get_unique_child_name(self, name, parent):
        """ Returns a unique name by treating the names as unique integers
        and returning the next value.

        """

        names = sorted([
            int(result[0]) for result in self.session.query(Category.name)
            if result[0].isdigit()
        ])
        next = (names[-1] + 1) if names else 1
        return str(next)

    def as_options(self, active_only=True):
        """ Returns an ordered list of (active) categories which can be used
        for selects.

        """

        def title(item):
            return item.title if item.active else '({})'.format(item.title)

        query = self.query()
        if active_only:
            query = query.filter(Category.active.is_(True))
        query = query.order_by(Category.order)
        return [(category.name, title(category)) for category in query]
