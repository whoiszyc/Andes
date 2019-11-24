import logging
import numpy as np
logger = logging.getLogger(__name__)


class GroupBase(object):
    """
    Base class for groups
    """

    def __init__(self):
        self.common_params = ['u', 'name']
        self.common_vars = []

        self.models = {}  # model name, model instance
        self._idx2model = {}  # element idx, model name

    @property
    def class_name(self):
        return self.__class__.__name__

    def add_model(self, name, instance):
        if name not in self.models:
            self.models[name] = instance
        else:
            raise KeyError(f"Duplicate model registration if {name}")

    def add(self, idx, model):
        """
        Register an idx from model_name to the group

        Parameters
        ----------
        idx: Union[str, float, int]
            Register an element to a model

        model: Model
            instance of the model

        Returns
        -------

        """
        if idx in self._idx2model:
            raise KeyError(f'Group <{self.class_name}> already contains <{repr(idx)}> from '
                           f'<{self._idx2model[idx].class_name}>')
        self._idx2model[idx] = model

    def idx2model(self, idx):
        ret = []
        for i in idx:
            try:
                ret.append(self._idx2model[i])
            except KeyError:
                raise KeyError(f'Group <{self.class_name}> does not contain idx <{i}>')
        return ret

    def get(self, src: str, idx, attr: str):
        """
        Based on the indexer, get the `attr` field of the `src` parameter or variable.

        Parameters
        ----------
        src : str
            param or var name
        idx : array-like

        attr
            The attribute of the param or var to retrieve

        Returns
        -------
        The requested param or variable attribute
        """
        self._check_src(src)
        self._check_idx(idx)

        n = len(idx)
        if n == 0:
            return np.zeros(0)

        ret = None
        models = self.idx2model(idx)
        for i, idx in enumerate(idx):
            uid = models[i].idx2uid(idx)
            instance = models[i].__dict__[src]
            val = instance.__dict__[attr][uid]

            # deduce the type for ret
            if ret is None:
                if isinstance(val, str):
                    ret = [''] * n
                else:
                    ret = np.zeros(n)
            ret[i] = val

        return ret

    def set(self, src: str, idx, attr, value):
        self._check_src(src)
        self._check_idx(idx)

        if isinstance(value, (float, str, int)):
            value = [value] * len(idx)

        models = self.idx2model(idx)
        for i, idx in enumerate(idx):
            model = models[i]
            uid = model.idx2uid(idx)
            instance = model.__dict__[src]
            instance.__dict__[attr][uid] = value[i]

    def _check_src(self, src: str):
        if src not in self.common_vars + self.common_params:
            raise AttributeError(f'Group <{self.class_name}> unable to get variable <{src}>')

    def _check_idx(self, idx):
        if idx is None:
            raise IndexError(f'{self.__class__.__name__}: idx cannot be None')

    def get_next_idx(self, idx=None, model_name=None):
        """
        Return the auto-generated next idx

        Parameters
        ----------
        idx

        model_name

        Returns
        -------

        """
        if model_name is None:
            model_name = self.class_name

        need_new = False

        if idx is not None:
            if idx not in self._idx2model:
                # name is good
                pass
            else:
                logger.debug(f"{self.class_name}: conflict idx {idx}. Data may be inconsistent.")
                need_new = True
        else:
            need_new = True

        if need_new is True:
            count = len(self._idx2model)
            while True:
                idx = model_name + '_' + str(count)
                if idx not in self._idx2model:
                    break
                else:
                    count += 1

        return idx


class Undefined(GroupBase):
    pass


class AcTopology(GroupBase):
    def __init__(self):
        super().__init__()
        self.common_vars.extend(('a', 'v'))


class StaticGen(GroupBase):
    def __init__(self):
        super().__init__()
        self.common_params.extend(('p0', 'q0'))
        self.common_vars.extend(('p', 'q', 'a', 'v'))


class AcLine(GroupBase):
    pass


class StaticLoad(GroupBase):
    pass


class StaticShunt(GroupBase):
    pass


class SynGen(GroupBase):
    pass
