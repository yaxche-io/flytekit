from __future__ import absolute_import

from flytekit.common import workflow, constants, promise
from flytekit.common.types import primitives
from flytekit.models.core import workflow as _workflow_models, identifier as _identifier
from flytekit.sdk.tasks import python_task, inputs, outputs

import pytest as _pytest


def test_output():
    o = workflow.Output('name', 1, sdk_type=primitives.Integer, help="blah")
    assert o.name == 'name'
    assert o.var.description == "blah"
    assert o.var.type == primitives.Integer.to_flyte_literal_type()
    assert o.binding_data.scalar.primitive.integer == 1


def test_workflow():

    @inputs(a=primitives.Integer)
    @outputs(b=primitives.Integer)
    @python_task()
    def my_task(wf_params, a, b):
        b.set(a + 1)

    my_task._id = _identifier.Identifier(_identifier.ResourceType.TASK, 'propject', 'domain', 'my_task', 'version')

    @inputs(a=[primitives.Integer])
    @outputs(b=[primitives.Integer])
    @python_task
    def my_list_task(wf_params, a, b):
        b.set([v + 1 for v in a])

    my_list_task._id = _identifier.Identifier(_identifier.ResourceType.TASK, 'propject', 'domain', 'my_list_task',
                                              'version')

    input_list = [
        promise.Input('input_1', primitives.Integer),
        promise.Input('input_2', primitives.Integer, default=5, help='Not required.')
    ]

    n1 = my_task(a=input_list[0]).assign_id_and_return('n1')
    n2 = my_task(a=input_list[1]).assign_id_and_return('n2')
    n3 = my_task(a=100).assign_id_and_return('n3')
    n4 = my_task(a=n1.outputs.b).assign_id_and_return('n4')
    n5 = my_list_task(a=[input_list[0], input_list[1], n3.outputs.b, 100]).assign_id_and_return('n5')
    n6 = my_list_task(a=n5.outputs.b)
    n1 >> n6

    nodes = [n1, n2, n3, n4, n5, n6]

    w = workflow.SdkWorkflow(
        inputs=input_list,
        outputs=[workflow.Output('a', n1.outputs.b, sdk_type=primitives.Integer)],
        nodes=nodes
    )

    assert w.interface.inputs['input_1'].type == primitives.Integer.to_flyte_literal_type()
    assert w.interface.inputs['input_2'].type == primitives.Integer.to_flyte_literal_type()
    assert w.nodes[0].inputs[0].var == 'a'
    assert w.nodes[0].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[0].inputs[0].binding.promise.var == 'input_1'
    assert w.nodes[1].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[1].inputs[0].binding.promise.var == 'input_2'
    assert w.nodes[2].inputs[0].binding.scalar.primitive.integer == 100
    assert w.nodes[3].inputs[0].var == 'a'
    assert w.nodes[3].inputs[0].binding.promise.node_id == n1.id

    # Test conversion to flyte_idl and back
    w._id = _identifier.Identifier(_identifier.ResourceType.WORKFLOW, 'fake', 'faker', 'fakest', 'fakerest')
    w = _workflow_models.WorkflowTemplate.from_flyte_idl(w.to_flyte_idl())
    assert w.interface.inputs['input_1'].type == primitives.Integer.to_flyte_literal_type()
    assert w.interface.inputs['input_2'].type == primitives.Integer.to_flyte_literal_type()
    assert w.nodes[0].inputs[0].var == 'a'
    assert w.nodes[0].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[0].inputs[0].binding.promise.var == 'input_1'
    assert w.nodes[1].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[1].inputs[0].binding.promise.var == 'input_2'
    assert w.nodes[2].inputs[0].binding.scalar.primitive.integer == 100
    assert w.nodes[3].inputs[0].var == 'a'
    assert w.nodes[3].inputs[0].binding.promise.node_id == n1.id
    assert w.nodes[4].inputs[0].var == 'a'
    assert w.nodes[4].inputs[0].binding.collection.bindings[0].promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[4].inputs[0].binding.collection.bindings[0].promise.var == 'input_1'
    assert w.nodes[4].inputs[0].binding.collection.bindings[1].promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[4].inputs[0].binding.collection.bindings[1].promise.var == 'input_2'
    assert w.nodes[4].inputs[0].binding.collection.bindings[2].promise.node_id == n3.id
    assert w.nodes[4].inputs[0].binding.collection.bindings[2].promise.var == 'b'
    assert w.nodes[4].inputs[0].binding.collection.bindings[3].scalar.primitive.integer == 100
    assert w.nodes[5].inputs[0].var == 'a'
    assert w.nodes[5].inputs[0].binding.promise.node_id == n5.id
    assert w.nodes[5].inputs[0].binding.promise.var == 'b'

    assert len(w.outputs) == 1
    assert w.outputs[0].var == 'a'
    assert w.outputs[0].binding.promise.var == 'b'
    assert w.outputs[0].binding.promise.node_id == 'n1'
    # TODO: Test promotion of w -> SdkWorkflow


def test_workflow_decorator():
    @inputs(a=primitives.Integer)
    @outputs(b=primitives.Integer)
    @python_task
    def my_task(wf_params, a, b):
        b.set(a + 1)

    my_task._id = _identifier.Identifier(_identifier.ResourceType.TASK, 'propject', 'domain', 'my_task', 'version')

    @inputs(a=[primitives.Integer])
    @outputs(b=[primitives.Integer])
    @python_task
    def my_list_task(wf_params, a, b):
        b.set([v + 1 for v in a])

    my_list_task._id = _identifier.Identifier(_identifier.ResourceType.TASK, 'propject', 'domain', 'my_list_task',
                                              'version')

    class my_workflow(object):
        input_1 = promise.Input('input_1', primitives.Integer)
        input_2 = promise.Input('input_2', primitives.Integer, default=5, help='Not required.')
        n1 = my_task(a=input_1)
        n2 = my_task(a=input_2)
        n3 = my_task(a=100)
        n4 = my_task(a=n1.outputs.b)
        n5 = my_list_task(a=[input_1, input_2, n3.outputs.b, 100])
        n6 = my_list_task(a=n5.outputs.b)
        n1 >> n6
        a = workflow.Output('a', n1.outputs.b, sdk_type=primitives.Integer)

    w = workflow.build_sdk_workflow_from_metaclass(my_workflow)

    assert w.interface.inputs['input_1'].type == primitives.Integer.to_flyte_literal_type()
    assert w.interface.inputs['input_2'].type == primitives.Integer.to_flyte_literal_type()
    assert w.nodes[0].inputs[0].var == 'a'
    assert w.nodes[0].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[0].inputs[0].binding.promise.var == 'input_1'
    assert w.nodes[1].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[1].inputs[0].binding.promise.var == 'input_2'
    assert w.nodes[2].inputs[0].binding.scalar.primitive.integer == 100
    assert w.nodes[3].inputs[0].var == 'a'
    assert w.nodes[3].inputs[0].binding.promise.node_id == 'n1'

    # Test conversion to flyte_idl and back
    w._id = _identifier.Identifier(_identifier.ResourceType.WORKFLOW, 'fake', 'faker', 'fakest', 'fakerest')
    w = _workflow_models.WorkflowTemplate.from_flyte_idl(w.to_flyte_idl())
    assert w.interface.inputs['input_1'].type == primitives.Integer.to_flyte_literal_type()
    assert w.interface.inputs['input_2'].type == primitives.Integer.to_flyte_literal_type()
    assert w.nodes[0].inputs[0].var == 'a'
    assert w.nodes[0].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[0].inputs[0].binding.promise.var == 'input_1'
    assert w.nodes[1].inputs[0].binding.promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[1].inputs[0].binding.promise.var == 'input_2'
    assert w.nodes[2].inputs[0].binding.scalar.primitive.integer == 100
    assert w.nodes[3].inputs[0].var == 'a'
    assert w.nodes[3].inputs[0].binding.promise.node_id == 'n1'
    assert w.nodes[4].inputs[0].var == 'a'
    assert w.nodes[4].inputs[0].binding.collection.bindings[0].promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[4].inputs[0].binding.collection.bindings[0].promise.var == 'input_1'
    assert w.nodes[4].inputs[0].binding.collection.bindings[1].promise.node_id == constants.GLOBAL_INPUT_NODE_ID
    assert w.nodes[4].inputs[0].binding.collection.bindings[1].promise.var == 'input_2'
    assert w.nodes[4].inputs[0].binding.collection.bindings[2].promise.node_id == 'n3'
    assert w.nodes[4].inputs[0].binding.collection.bindings[2].promise.var == 'b'
    assert w.nodes[4].inputs[0].binding.collection.bindings[3].scalar.primitive.integer == 100
    assert w.nodes[5].inputs[0].var == 'a'
    assert w.nodes[5].inputs[0].binding.promise.node_id == 'n5'
    assert w.nodes[5].inputs[0].binding.promise.var == 'b'

    assert len(w.outputs) == 1
    assert w.outputs[0].var == 'a'
    assert w.outputs[0].binding.promise.var == 'b'
    assert w.outputs[0].binding.promise.node_id == 'n1'
    # TODO: Test promotion of w -> SdkWorkflow


def test_workflow_node():
    @inputs(a=primitives.Integer)
    @outputs(b=primitives.Integer)
    @python_task()
    def my_task(wf_params, a, b):
        b.set(a + 1)

    my_task._id = _identifier.Identifier(_identifier.ResourceType.TASK, 'project', 'domain', 'my_task', 'version')

    @inputs(a=[primitives.Integer])
    @outputs(b=[primitives.Integer])
    @python_task
    def my_list_task(wf_params, a, b):
        b.set([v + 1 for v in a])

    my_list_task._id = _identifier.Identifier(_identifier.ResourceType.TASK, 'project', 'domain', 'my_list_task',
                                              'version')

    input_list = [
        promise.Input('required', primitives.Integer),
        promise.Input('not_required', primitives.Integer, default=5, help='Not required.')
    ]

    n1 = my_task(a=input_list[0]).assign_id_and_return('n1')
    n2 = my_task(a=input_list[1]).assign_id_and_return('n2')
    n3 = my_task(a=100).assign_id_and_return('n3')
    n4 = my_task(a=n1.outputs.b).assign_id_and_return('n4')
    n5 = my_list_task(a=[input_list[0], input_list[1], n3.outputs.b, 100]).assign_id_and_return('n5')
    n6 = my_list_task(a=n5.outputs.b)

    nodes = [n1, n2, n3, n4, n5, n6]

    wf_out = [
        workflow.Output(
            'nested_out',
            [n5.outputs.b, n6.outputs.b, [n1.outputs.b, n2.outputs.b]],
            sdk_type=[[primitives.Integer]]
        ),
        workflow.Output('scalar_out', n1.outputs.b, sdk_type=primitives.Integer)
    ]

    w = workflow.SdkWorkflow(inputs=input_list, outputs=wf_out, nodes=nodes)

    with _pytest.raises(NotImplementedError):
        w()

    # TODO: Uncomment when sub-workflows are supported.
    """
    # Test that required input isn't set
    with _pytest.raises(_user_exceptions.FlyteAssertion):
        w()

    # Test that positional args are rejected
    with _pytest.raises(_user_exceptions.FlyteAssertion):
        w(1, 2)

    # Test that type checking works
    with _pytest.raises(_user_exceptions.FlyteTypeException):
        w(required='abc', not_required=1)

    # Test that bad arg name is detected
    with _pytest.raises(_user_exceptions.FlyteAssertion):
        w(required=1, bad_arg=1)

    # Test default input is accounted for
    n = w(required=10)
    assert n.inputs[0].var == 'not_required'
    assert n.inputs[0].binding.scalar.primitive.integer == 5
    assert n.inputs[1].var == 'required'
    assert n.inputs[1].binding.scalar.primitive.integer == 10

    # Test default input is overridden
    n = w(required=10, not_required=50)
    assert n.inputs[0].var == 'not_required'
    assert n.inputs[0].binding.scalar.primitive.integer == 50
    assert n.inputs[1].var == 'required'
    assert n.inputs[1].binding.scalar.primitive.integer == 10

    # Test that launch plan ID ref is flexible
    w._id = 'fake'
    assert n.workflow_node.sub_workflow_ref == 'fake'
    w._id = None

    # Test that outputs are promised
    n.assign_id_and_return('node-id')
    assert n.outputs['scalar_out'].sdk_type.to_flyte_literal_type() == primitives.Integer.to_flyte_literal_type()
    assert n.outputs['scalar_out'].var == 'scalar_out'
    assert n.outputs['scalar_out'].node_id == 'node-id'

    assert n.outputs['nested_out'].sdk_type.to_flyte_literal_type() == \
        containers.List(containers.List(primitives.Integer)).to_flyte_literal_type()
    assert n.outputs['nested_out'].var == 'nested_out'
    assert n.outputs['nested_out'].node_id == 'node-id'
    """
