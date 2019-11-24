from typing import Optional, Union, Callable

import numpy as np
import logging
from andes.devices.group import GroupBase

logger = logging.getLogger(__name__)


class ParamBase(object):
    """
    Base parameter class for storing non-computational parameters

    Parameters
    ----------
    default : str or float
        The default value of this parameter if no value is provided
    name : str
        Name of this parameter. If not provided, `name` will be set
        to the attribute name of the parent `Model`.
    tex_name : str
        LaTeX-formatted parameter name. If not provided, `tex_name`
        will be assigned the same as `name`.
    info : str
        A description of this parameter
    mandatory : bool
        True if this parameter is mandatory
    """
    def __init__(self,
                 default=None,
                 name=None,
                 tex_name=None,
                 info=None,
                 mandatory: bool = False,
                 export: bool = True):
        self.name = name
        self.default = default
        self.tex_name = tex_name if tex_name else name
        self.info = info
        self.owner = None
        self.export = export

        # self.n = 0
        self.v = []
        self.property = dict(mandatory=mandatory)

    def add(self, value=None):
        """
        Add a new value (from a new element) to this parameter list

        Parameters
        ----------
        value : str or float
            Parameter value of the new element

        Returns
        -------
        None
        """

        # check for mandatory
        if value is None:
            if self.get_property('mandatory'):
                raise ValueError(f'Mandatory parameter {self.name} missing')
            else:
                value = self.default

        if isinstance(self.v, list):
            self.v.append(value)
        else:
            np.append(self.v, value)

        # self.n += 1

    @property
    def n(self):
        return len(self.v) if self.v else 0

    def get_property(self, property_name: str):
        """
        Check the boolean value of the given property

        Parameters
        ----------
        property_name : str
            Property name

        Returns
        -------
        The truth value of the property
        """
        return self.property[property_name]

    def get_name(self):
        """
        Return `name` in a list

        Returns
        -------
        list
            A list only containing the name of the parameter
        """
        return [self.name]


class DataParam(ParamBase):
    """
    An alias of the `ParamBase` class.

    This class is used for string parameters or non-computational
    numerical parameters. This class does not provide a `to_array`
    method. All input values will be stored in `v` as a list.
    """
    pass


class RefParam(ParamBase):
    def __init__(self, **kwargs):
        super(RefParam, self).__init__(**kwargs)
        self.export = False


class IdxParam(ParamBase):
    """
    A special ParamBase for storing `idx` of other models
    """
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model


class NumParam(ParamBase):
    """
    A computational numerical parameter.

    Parameters defined using
    this class will have their values converted to a NumPy.ndarray
    and stored in `v`. The original input values will be stored in
    `vin`, and the coefficients for converting to system-base per-unit
    will be stored in `pu_coeff`.


    Parameters
    ----------
    default : str or float
        The default value of this parameter if no value is provided
    name : str
        Name of this parameter. If not provided, `name` will be set
        to the attribute name of the parent `Model`.
    tex_name : str
        LaTeX-formatted parameter name. If not provided, `tex_name`
        will be assigned the same as `name`.
    info : str
        A description of this parameter
    mandatory : bool
        True if this parameter is mandatory
    unit : str
        Unit of the parameter

    Other Parameters
    ----------------
    non_zero : bool
        True if this parameter must be non-zero
    mandatory : bool
        True if this parameter must not be None
    power : bool
        True if this parameter is a power per-unit quantity
        under the device base
    voltage : bool
        True if the parameter is a voltage pu quantity
        under the device base
    current: bool
        True if the parameter is a current pu quantity
        under the device base
    z : bool
        True if the parameter is an AC impedance pu quantity
        under the device base
    y : bool
        True if the parameter is an AC admittance pu quantity
        under the device base
    r : bool
        True if the parameter is a DC resistance pu quantity
        under the device base
    g : bool
        True if the parameter is a DC conductance pu quantity
        under the device base
    dc_current : bool
        True if the parameter is a DC current pu quantity under
        device base
    dc_voltage : bool
        True if the parameter is a DC voltage pu quantity under
        device base
    """

    def __init__(self,
                 default: Optional[Union[float, str, Callable]] = None,
                 name: Optional[str] = None,
                 tex_name: Optional[str] = None,
                 info: Optional[str] = None,
                 unit: Optional[str] = None,
                 non_zero: bool = False,
                 mandatory: bool = False,
                 power: bool = False,
                 voltage: bool = False,
                 current: bool = False,
                 z: bool = False,
                 y: bool = False,
                 r: bool = False,
                 g: bool = False,
                 dc_voltage: bool = False,
                 dc_current: bool = False,
                 export: bool = True,
                 ):
        super(NumParam, self).__init__(default=default, name=name, tex_name=tex_name, info=info, export=export)
        self.unit = unit

        self.property = dict(non_zero=non_zero,
                             mandatory=mandatory,
                             power=power,
                             voltage=voltage,
                             current=current,
                             z=z,
                             y=y,
                             r=r,
                             g=g,
                             dc_current=dc_current,
                             dc_voltage=dc_voltage)

        self.pu_coeff = np.ndarray([])
        self.vin = None  # values from input

    def add(self, value=None):
        """
        Add a new value (from a new element) to this parameter list

        Parameters
        ----------
        value : str or float
            Parameter value of the new element

        Returns
        -------
        None
        """

        # check for mandatory
        if value is None:
            if self.get_property('mandatory'):
                raise ValueError(f'Mandatory parameter {self.name} missing')
            else:
                value = self.default
        elif isinstance(value, str):
            value = float(value)

        # check for non-zero
        if value == 0.0 and self.get_property('non_zero'):
            logger.warning(f'Parameter {self.name} must be non-zero')
            value = self.default

        super(NumParam, self).add(value)

    def to_array(self):
        """
        Convert `v` to np.ndarray after adding elements. Store a copy
        if the input in `vin`.

        The conversion enables array-based calculation.

        Warnings
        --------
        After this call, `add` will not be allowed.
        """
        self.v = np.array(self.v)
        self.vin = np.array(self.v)

    def restore(self):
        self.v = self.vin


class ExtParam(NumParam):
    """
    A parameter whose values are retrieved from an external model.

    Parameters
    ----------
    model : str
        Name of the source model
    src : str
        Source parameter name
    indexer : ParamBase
        A parameter of the hosting model, used as indices into
        the source model and parameter. If is None, the source
        parameter values will be fully copied.

    Attributes
    ----------
    parent_model : Model
        The parent model providing the original parameter.
    parent_instance : ParamBase
        The parent parameter, which is an attribute of the parent
        model, providing the original values.
    uid : array-like
        An array containing the absolute indices into the
        parent_instance values.
    """
    def __init__(self,
                 model: str,
                 src: str,
                 indexer=None,
                 **kwargs):
        super(ExtParam, self).__init__(**kwargs)
        self.model = model
        self.src = src
        self.indexer = indexer
        self.parent_model = None   # parent model instance

    def link_external(self, ext_model):
        """
        Update parameter values provided by external models

        Parameters
        ----------
        ext_model : Model
            Instance of the parent model

        Returns
        -------
        None
        """
        self.parent_model = ext_model

        if isinstance(ext_model, GroupBase):

            # TODO: the three lines below is a bit inefficient - 3x same loops
            self.v = ext_model.get(src=self.src, idx=self.indexer.v, attr='v')
            self.vin = ext_model.get(src=self.src, idx=self.indexer.v, attr='vin')
            # TODO: uncomment when pu_coeff() is ready
            # self.pu_coeff = ext_model.get(src=self.src, idx=self.indexer.v, attr='vin')

        else:
            parent_instance = ext_model.__dict__[self.src]
            self.property = dict(parent_instance.property)

            if self.indexer is None:
                # if `idx` is None, retrieve all the values
                uid = np.arange(ext_model.n)
            else:
                if len(self.indexer.v) == 0:
                    return
                else:
                    uid = ext_model.idx2uid(self.indexer.v)

            # pull in values
            self.v = parent_instance.v[uid]
            self.vin = parent_instance.vin[uid]
            # TODO: uncomment when pu_coeff() is ready
            # self.pu_coeff = parent_instance.pu_coeff[uid]
