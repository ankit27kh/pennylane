# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This module contains the qml.measure measurement.
"""
import uuid
from collections.abc import Hashable
from functools import lru_cache
from typing import Generic, Optional, TypeVar, Union

import pennylane as qml
from pennylane.wires import Wires

from .measurements import MeasurementProcess


def measure(wires: Union[Hashable, Wires], reset: bool = False, postselect: Optional[int] = None):
    r"""Perform a mid-circuit measurement in the computational basis on the
    supplied qubit.

    Computational basis measurements are performed using the 0, 1 convention
    rather than the ±1 convention.
    Measurement outcomes can be used to conditionally apply operations, and measurement
    statistics can be gathered and returned by a quantum function.

    If a device doesn't support mid-circuit measurements natively, then the
    QNode will apply the :func:`defer_measurements` transform.

    **Example:**

    .. code-block:: python3

        dev = qml.device("default.qubit", wires=3)

        @qml.qnode(dev)
        def func(x, y):
            qml.RY(x, wires=0)
            qml.CNOT(wires=[0, 1])
            m_0 = qml.measure(1)

            qml.cond(m_0, qml.RY)(y, wires=0)
            return qml.probs(wires=[0])

    Executing this QNode:

    >>> pars = np.array([0.643, 0.246], requires_grad=True)
    >>> func(*pars)
    tensor([0.90165331, 0.09834669], requires_grad=True)

    Wires can be reused after measurement. Moreover, measured wires can be reset
    to the :math:`|0 \rangle` state by setting ``reset=True``.

    .. code-block:: python3

        dev = qml.device("default.qubit", wires=3)

        @qml.qnode(dev)
        def func():
            qml.X(1)
            m_0 = qml.measure(1, reset=True)
            return qml.probs(wires=[1])

    Executing this QNode:

    >>> func()
    tensor([1., 0.], requires_grad=True)

    Mid-circuit measurements can be manipulated using the following arithmetic operators:
    ``+``, ``-``, ``*``, ``/``, ``~`` (not), ``&`` (and), ``|`` (or), ``==``, ``<=``,
    ``>=``, ``<``, ``>`` with other mid-circuit measurements or scalars.

    .. Note ::

        Python ``not``, ``and``, ``or``, do not work since these do not have dunder methods.
        Instead use ``~``, ``&``, ``|``.

    Mid-circuit measurement results can be processed with the usual measurement functions such as
    :func:`~.expval`. For QNodes with finite shots, :func:`~.sample` applied to a mid-circuit measurement
    result will return a binary sequence of samples.
    See :ref:`here <mid_circuit_measurements_statistics>` for more details.

    .. Note ::

        Computational basis measurements are performed using the 0, 1 convention rather than the ±1 convention.
        So, for example, ``expval(qml.measure(0))`` and ``expval(qml.Z(0))`` will give different answers.

    .. code-block:: python3

        dev = qml.device("default.qubit")

        @qml.qnode(dev)
        def circuit(x, y):
            qml.RX(x, wires=0)
            qml.RY(y, wires=1)
            m0 = qml.measure(1)
            return (
                qml.sample(m0), qml.expval(m0), qml.var(m0), qml.probs(op=m0), qml.counts(op=m0),
            )

    >>> circuit(1.0, 2.0, shots=1000)
    (array([0, 1, 1, ..., 1, 1, 1])), 0.702, 0.20919600000000002, array([0.298, 0.702]), {0: 298, 1: 702})

    Args:
        wires (Wires): The wire to measure.
        reset (Optional[bool]): Whether to reset the wire to the :math:`|0 \rangle`
            state after measurement.
        postselect (Optional[int]): Which basis state to postselect after a mid-circuit
            measurement. None by default. If postselection is requested, only the post-measurement
            state that is used for postselection will be considered in the remaining circuit.

    Returns:
        MidMeasureMP: measurement process instance

    Raises:
        QuantumFunctionError: if multiple wires were specified

    .. details::
        :title: Postselection

        Postselection discards outcomes that do not meet the criteria provided by the ``postselect``
        argument. For example, specifying ``postselect=1`` on wire 0 would be equivalent to projecting
        the state vector onto the :math:`|1\rangle` state on wire 0:

        .. code-block:: python3

            dev = qml.device("default.qubit")

            @qml.qnode(dev)
            def func(x):
                qml.RX(x, wires=0)
                m0 = qml.measure(0, postselect=1)
                qml.cond(m0, qml.X)(wires=1)
                return qml.sample(wires=1)

        By postselecting on ``1``, we only consider the ``1`` measurement outcome on wire 0. So, the probability of
        measuring ``1`` on wire 1 after postselection should also be 1. Executing this QNode with 10 shots:

        >>> func(np.pi / 2, shots=10)
        array([1, 1, 1, 1, 1, 1, 1])

        Note that only 7 samples are returned. This is because samples that do not meet the postselection criteria are
        thrown away.

        If postselection is requested on a state with zero probability of being measured, the result may contain ``NaN``
        or ``Inf`` values:

        .. code-block:: python3

            dev = qml.device("default.qubit")

            @qml.qnode(dev)
            def func(x):
                qml.RX(x, wires=0)
                m0 = qml.measure(0, postselect=1)
                qml.cond(m0, qml.X)(wires=1)
                return qml.probs(wires=1)

        >>> func(0.0)
        tensor([nan, nan], requires_grad=True)

        In the case of ``qml.sample``, an empty array will be returned:

        .. code-block:: python3

            dev = qml.device("default.qubit")

            @qml.qnode(dev)
            def func(x):
                qml.RX(x, wires=0)
                m0 = qml.measure(0, postselect=1)
                qml.cond(m0, qml.X)(wires=1)
                return qml.sample(wires=[0, 1])

        >>> func(0.0, shots=[10, 10])
        (array([], shape=(0, 2), dtype=int64), array([], shape=(0, 2), dtype=int64))

        .. note::

            Currently, postselection support is only available on ``default.qubit``. Using postselection
            on other devices will raise an error.

        .. warning::

            All measurements are supported when using postselection. However, postselection on a zero probability
            state can cause some measurements to break:

            * With finite shots, one must be careful when measuring ``qml.probs`` or ``qml.counts``, as these
              measurements will raise errors if there are no valid samples after postselection. This will occur
              with postselection states that have zero or close to zero probability.

            * With analytic execution, ``qml.mutual_info`` will raise errors when using any interfaces except
              ``jax``, and ``qml.vn_entropy`` will raise an error with the ``tensorflow`` interface when the
              postselection state has zero probability.

            * When using JIT, ``QNode``'s may have unexpected behaviour when postselection on a zero
              probability state is performed. Due to floating point precision, the zero probability may not be
              detected, thus letting execution continue as normal without ``NaN`` or ``Inf`` values or empty
              samples, leading to unexpected or incorrect results.

    """
    if qml.capture.enabled():
        primitive = _create_mid_measure_primitive()
        return primitive.bind(wires, reset=reset, postselect=postselect)

    return _measure_impl(wires, reset=reset, postselect=postselect)


def _measure_impl(
    wires: Union[Hashable, Wires], reset: Optional[bool] = False, postselect: Optional[int] = None
):
    """Concrete implementation of qml.measure"""
    wires = Wires(wires)
    if len(wires) > 1:
        raise qml.QuantumFunctionError(
            "Only a single qubit can be measured in the middle of the circuit"
        )

    # Create a UUID and a map between MP and MV to support serialization
    measurement_id = str(uuid.uuid4())
    mp = MidMeasureMP(wires=wires, reset=reset, postselect=postselect, id=measurement_id)
    return MeasurementValue([mp], processing_fn=lambda v: v)


@lru_cache
def _create_mid_measure_primitive():
    """Create a primitive corresponding to an mid-circuit measurement type.

    Called when using :func:`~pennylane.measure`.

    Returns:
        jax.core.Primitive: A new jax primitive corresponding to a mid-circuit
        measurement.

    """
    # pylint: disable=import-outside-toplevel
    import jax

    from pennylane.capture.custom_primitives import NonInterpPrimitive

    mid_measure_p = NonInterpPrimitive("measure")

    @mid_measure_p.def_impl
    def _(wires, reset=False, postselect=None):
        return _measure_impl(wires, reset=reset, postselect=postselect)

    @mid_measure_p.def_abstract_eval
    def _(*_, **__):
        dtype = jax.numpy.int64 if jax.config.jax_enable_x64 else jax.numpy.int32
        return jax.core.ShapedArray((), dtype)

    return mid_measure_p


T = TypeVar("T")


class MidMeasureMP(MeasurementProcess):
    """Mid-circuit measurement.

    This class additionally stores information about unknown measurement outcomes in the qubit model.
    Measurements on a single qubit in the computational basis are assumed.

    Please refer to :func:`pennylane.measure` for detailed documentation.

    Args:
        wires (.Wires): The wires the measurement process applies to.
            This can only be specified if an observable was not provided.
        reset (bool): Whether to reset the wire after measurement.
        postselect (Optional[int]): Which basis state to postselect after a mid-circuit
            measurement. None by default. If postselection is requested, only the post-measurement
            state that is used for postselection will be considered in the remaining circuit.
        id (str): Custom label given to a measurement instance.
    """

    _shortname = "measure"

    def _flatten(self):
        metadata = (("wires", self.raw_wires), ("reset", self.reset), ("id", self.id))
        return (None, None), metadata

    def __init__(
        self,
        wires: Optional[Wires] = None,
        reset: Optional[bool] = False,
        postselect: Optional[int] = None,
        id: Optional[str] = None,
    ):
        self.batch_size = None
        super().__init__(wires=Wires(wires), id=id)
        self.reset = reset
        self.postselect = postselect

    # pylint: disable=arguments-renamed, arguments-differ
    @classmethod
    def _primitive_bind_call(cls, wires=None, reset=False, postselect=None, id=None):
        wires = () if wires is None else wires
        return cls._wires_primitive.bind(*wires, reset=reset, postselect=postselect, id=id)

    @classmethod
    def _abstract_eval(
        cls,
        n_wires: Optional[int] = None,
        has_eigvals=False,
        shots: Optional[int] = None,
        num_device_wires: int = 0,
    ) -> tuple:
        return (), int

    def label(self, decimals=None, base_label=None, cache=None):  # pylint: disable=unused-argument
        r"""How the mid-circuit measurement is represented in diagrams and drawings.

        Args:
            decimals=None (Int): If ``None``, no parameters are included. Else,
                how to round the parameters.
            base_label=None (Iterable[str]): overwrite the non-parameter component of the label.
                Must be same length as ``obs`` attribute.
            cache=None (dict): dictionary that carries information between label calls
                in the same drawing

        Returns:
            str: label to use in drawings
        """
        _label = "┤↗"
        if self.postselect is not None:
            _label += "₁" if self.postselect == 1 else "₀"

        _label += "├" if not self.reset else "│  │0⟩"

        return _label

    @property
    def samples_computational_basis(self):
        return False

    @property
    def _queue_category(self):
        return "_ops"

    @property
    def hash(self):
        """int: Returns an integer hash uniquely representing the measurement process"""
        fingerprint = (
            self.__class__.__name__,
            tuple(self.wires.tolist()),
            self.id,
        )

        return hash(fingerprint)

    @property
    def data(self):
        """The data of the measurement. Needed to match the Operator API."""
        return []

    @property
    def name(self):
        """The name of the measurement. Needed to match the Operator API."""
        return self.__class__.__name__

    @property
    def num_params(self):
        """The number of parameters. Needed to match the Operator API."""
        return 0


class MeasurementValue(Generic[T]):
    """A class representing unknown measurement outcomes in the qubit model.

    Measurements on a single qubit in the computational basis are assumed.

    Args:
        measurements (list[.MidMeasureMP]): The measurement(s) that this object depends on.
        processing_fn (callable): A lazily transformation applied to the measurement values.
    """

    name = "MeasurementValue"

    def __init__(self, measurements, processing_fn):
        self.measurements = measurements
        self.processing_fn = processing_fn

    def items(self):
        """A generator representing all the possible outcomes of the MeasurementValue."""
        num_meas = len(self.measurements)
        for i in range(2**num_meas):
            branch = tuple(int(b) for b in f"{i:0{num_meas}b}")
            yield branch, self.processing_fn(*branch)

    def postselected_items(self):
        """A generator representing all the possible outcomes of the MeasurementValue,
        taking postselection into account."""
        # pylint: disable=stop-iteration-return
        ps = {i: p for i, m in enumerate(self.measurements) if (p := m.postselect) is not None}
        num_non_ps = len(self.measurements) - len(ps)
        if num_non_ps == 0:
            yield (), self.processing_fn(*ps.values())
            return
        for i in range(2**num_non_ps):
            # Create the branch ignoring postselected measurements
            non_ps_branch = tuple(int(b) for b in f"{i:0{num_non_ps}b}")
            # We want a consumable iterable and the static tuple above
            non_ps_branch_iter = iter(non_ps_branch)
            # Extend the branch to include postselected measurements
            full_branch = tuple(
                ps[j] if j in ps else next(non_ps_branch_iter)
                for j in range(len(self.measurements))
            )
            # Return the reduced non-postselected branch and the procesing function
            # evaluated on the full branch
            yield non_ps_branch, self.processing_fn(*full_branch)

    @property
    def wires(self):
        """Returns a list of wires corresponding to the mid-circuit measurements."""
        return Wires.all_wires([m.wires for m in self.measurements])

    @property
    def branches(self):
        """A dictionary representing all possible outcomes of the MeasurementValue."""
        ret_dict = {}
        num_meas = len(self.measurements)
        for i in range(2**num_meas):
            branch = tuple(int(b) for b in f"{i:0{num_meas}b}")
            ret_dict[branch] = self.processing_fn(*branch)
        return ret_dict

    def map_wires(self, wire_map):
        """Returns a copy of the current ``MeasurementValue`` with the wires of each measurement changed
        according to the given wire map.

        Args:
            wire_map (dict): dictionary containing the old wires as keys and the new wires as values

        Returns:
            MeasurementValue: new ``MeasurementValue`` instance with measurement wires mapped
        """
        mapped_measurements = [m.map_wires(wire_map) for m in self.measurements]
        return MeasurementValue(mapped_measurements, self.processing_fn)

    def _transform_bin_op(self, base_bin, other):
        """Helper function for defining dunder binary operations."""
        if isinstance(other, MeasurementValue):
            # pylint: disable=protected-access
            return self._merge(other)._apply(lambda t: base_bin(t[0], t[1]))
        # if `other` is not a MeasurementValue then apply it to each branch
        return self._apply(lambda v: base_bin(v, other))

    def __invert__(self):
        """Return a copy of the measurement value with an inverted control
        value."""
        return self._apply(qml.math.logical_not)

    def __bool__(self) -> bool:
        raise ValueError(
            "The truth value of a MeasurementValue is undefined. To condition on a MeasurementValue, please use qml.cond instead."
        )

    def __eq__(self, other):
        return self._transform_bin_op(lambda a, b: a == b, other)

    def __ne__(self, other):
        return self._transform_bin_op(lambda a, b: a != b, other)

    def __add__(self, other):
        return self._transform_bin_op(lambda a, b: a + b, other)

    def __radd__(self, other):
        return self._apply(lambda v: other + v)

    def __sub__(self, other):
        return self._transform_bin_op(lambda a, b: a - b, other)

    def __rsub__(self, other):
        return self._apply(lambda v: other - v)

    def __mul__(self, other):
        return self._transform_bin_op(lambda a, b: a * b, other)

    def __rmul__(self, other):
        return self._apply(lambda v: other * qml.math.cast_like(v, other))

    def __truediv__(self, other):
        return self._transform_bin_op(lambda a, b: a / b, other)

    def __rtruediv__(self, other):
        return self._apply(lambda v: other / v)

    def __lt__(self, other):
        return self._transform_bin_op(lambda a, b: a < b, other)

    def __le__(self, other):
        return self._transform_bin_op(lambda a, b: a <= b, other)

    def __gt__(self, other):
        return self._transform_bin_op(lambda a, b: a > b, other)

    def __ge__(self, other):
        return self._transform_bin_op(lambda a, b: a >= b, other)

    def __and__(self, other):
        return self._transform_bin_op(qml.math.logical_and, other)

    def __or__(self, other):
        return self._transform_bin_op(qml.math.logical_or, other)

    def __mod__(self, other):
        return self._transform_bin_op(qml.math.mod, other)

    def __xor__(self, other):
        return self._transform_bin_op(qml.math.logical_xor, other)

    def _apply(self, fn):
        """Apply a post computation to this measurement"""
        return MeasurementValue(self.measurements, lambda *x: fn(self.processing_fn(*x)))

    def concretize(self, measurements: dict):
        """Returns a concrete value from a dictionary of hashes with concrete values."""
        values = tuple(measurements[meas] for meas in self.measurements)
        return self.processing_fn(*values)

    def _merge(self, other: "MeasurementValue"):
        """Merge two measurement values"""

        # create a new merged list with no duplicates and in lexical ordering
        merged_measurements = list(set(self.measurements).union(set(other.measurements)))
        merged_measurements.sort(key=lambda m: m.id)

        # create a new function that selects the correct indices for each sub function
        def merged_fn(*x):
            sub_args_1 = (x[i] for i in [merged_measurements.index(m) for m in self.measurements])
            sub_args_2 = (x[i] for i in [merged_measurements.index(m) for m in other.measurements])

            out_1 = self.processing_fn(*sub_args_1)
            out_2 = other.processing_fn(*sub_args_2)

            return out_1, out_2

        return MeasurementValue(merged_measurements, merged_fn)

    def __getitem__(self, i):
        branch = tuple(int(b) for b in f"{i:0{len(self.measurements)}b}")
        return self.processing_fn(*branch)

    def __str__(self):
        lines = []
        num_meas = len(self.measurements)
        for i in range(2**num_meas):
            branch = tuple(int(b) for b in f"{i:0{num_meas}b}")
            id_branch_mapping = [
                f"{self.measurements[j].id}={branch[j]}" for j in range(len(branch))
            ]
            lines.append(
                "if " + ",".join(id_branch_mapping) + " => " + str(self.processing_fn(*branch))
            )
        return "\n".join(lines)

    def __repr__(self):
        return f"MeasurementValue(wires={self.wires.tolist()})"


def get_mcm_predicates(conditions: tuple[MeasurementValue]) -> list[MeasurementValue]:
    r"""Function to make mid-circuit measurement predicates mutually exclusive.

    The ``conditions`` are predicates to the ``if`` and ``elif`` branches of ``qml.cond``.
    This function updates all the ``MeasurementValue``\ s in ``conditions`` such that
    reconciling the correct branch is never ambiguous.

    Args:
        conditions (Sequence[MeasurementValue]): Sequence containing predicates for ``if``
            and all ``elif`` branches of a function decorated with :func:`~pennylane.cond`.

    Returns:
        Sequence[MeasurementValue]: Updated sequence of mutually exclusive predicates.
    """
    new_conds = [conditions[0]]
    false_cond = ~conditions[0]

    for c in conditions[1:]:
        new_conds.append(false_cond & c)
        false_cond = false_cond & ~c

    new_conds.append(false_cond)
    return new_conds


def find_post_processed_mcms(circuit):
    """Return the subset of mid-circuit measurements which are required for post-processing.

    This includes any mid-circuit measurement that is post-selected or the object of a terminal
    measurement.
    """
    post_processed_mcms = set(
        op
        for op in circuit.operations
        if isinstance(op, MidMeasureMP) and op.postselect is not None
    )
    for m in circuit.measurements:
        if isinstance(m.mv, list):
            for mv in m.mv:
                post_processed_mcms = post_processed_mcms | set(mv.measurements)
        elif m.mv is not None:
            post_processed_mcms = post_processed_mcms | set(m.mv.measurements)
    return post_processed_mcms
