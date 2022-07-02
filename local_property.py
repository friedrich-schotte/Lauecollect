"""
Persistent property applications that are specific for each computer,
not global like "persistent_property"
    
Author: Friedrich Schotte
Date created: 2019-09-26
Date last modified: 2021-06-18
Revision comment: Cleanup
"""
__version__ = "1.3.3"


def local_property(name, default_value=0.0):
    from persistent_property_new import persistent_property
    return persistent_property("local.{name}." + name, default_value)


if __name__ == "__main__":
    import logging

    level = logging.DEBUG
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=msg_format)


    class Test(object):
        refresh_period = local_property("refresh_period", 1.0)


    self = Test()

    print('self.refresh_period')
    # print('type(self).refresh_period.dbname_template')
    # print('type(self).refresh_period.dbname(self)')
    print('type(self).refresh_period.filename(self)')
    print('')
