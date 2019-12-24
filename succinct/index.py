"""text indexes"""

import collections

class Index(collections.Sequence):
    """text index supporting search and count operations"""

    def __init__(self):
        # pylint: disable=super-init-not-called
        pass

    def __nonzero__(self):
        return len(self) > 0

    def __len__(self):
        raise NotImplementedError()

    def __getitem__(self, index):
        raise NotImplementedError()

    def indexes(self, string):
        raise NotImplementedError()
