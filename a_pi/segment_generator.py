"""Generation of a bounded segment
"""

import random


def random_segment(x_max, y_max):
    """Creates a segment with each endpoint x, y such that:

    .. math::

            x \\in [0;x\\_max],y \\in [0;y\\_max]
    """
    return (random.random()*x_max,
            random.random()*y_max,
            random.random()*x_max,
            random.random()*y_max)       
