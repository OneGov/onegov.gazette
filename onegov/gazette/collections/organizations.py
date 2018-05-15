from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.gazette.models import Organization


class OrganizationCollection(AdjacencyListCollection):
    """ Manage a list of organizations.

    The list is ordered manually (through migration and/or backend).

    """

    __listclass__ = Organization

    def get_unique_child_name(self, name, parent):
        """ Returns a unique name by treating the names as unique integers
        and returning the next value.

        """

        names = sorted([
            int(result[0]) for result in self.session.query(Organization.name)
            if result[0].isdigit()
        ])
        next = (names[-1] + 1) if names else 1
        return str(next)

    def as_options(self, active_only=True, grouped=False):
        """ Returns an ordered list of (active) organizations which can be used
        for selects.

        """

        def title(item):
            return item.title if item.active else '({})'.format(item.title)

        result = []
        result_grouped = []

        query = self.query()
        if active_only:
            query = query.filter(Organization.active.is_(True))
        query = query.filter(Organization.parent_id.is_(None))
        query = query.order_by(Organization.order)
        for root in query:
            if root.children:
                group = [
                    (child.name, title(child)) for child in root.children
                    if child.active or not active_only
                ]
                result.extend(group)
                result_grouped.append((title(root), group))
            else:
                result.append((root.name, title(root)))
                result_grouped.append((None, [(root.name, title(root))]))

        return result_grouped if grouped else result
