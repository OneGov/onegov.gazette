from yaml import load


class Principal(object):
    """ The principal is the political entity running the gazette app. """

    def __init__(
        self,
        name='',
        logo='',
        color='',
        on_accept=None,
        time_zone='Europe/Zurich',
        help_link='',
        publishing=False,
        frontend=False,
        sogc_import=None
    ):
        assert not on_accept or on_accept['mail_to']
        assert not frontend or (frontend and publishing)
        assert not sogc_import or (
            sogc_import['endpoint'] and
            sogc_import['username'] and
            sogc_import['password'] and
            sogc_import['canton'] and
            sogc_import['category'] and
            sogc_import['organization']
        )

        self.name = name
        self.logo = logo
        self.color = color
        self.on_accept = on_accept or {}
        self.time_zone = time_zone
        self.help_link = help_link
        self.publishing = publishing
        self.frontend = frontend
        self.sogc_import = sogc_import or {}

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))
