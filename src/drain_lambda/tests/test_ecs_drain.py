"""
Unit Tests for Drain Lambda function.
"""
import json
import os
import pytest
from botocore.stub import Stubber
import mock
from ecsdrain import drain


# pylint: disable=redefined-outer-name

@pytest.fixture
def test_params():
    """
    Test parameters fixture
    """
    test_params = {}
    test_params['ECS_STACK_NAME'] = 'sandbox-dev-0-ecs-cluster'
    test_params['ec2_instance_id'] = 'i-00682a39163dafc90'
    test_params['cluster_arn'] = 'arn:aws:ecs:us-west-2:631042910881:cluster/sandbox-dev-0-ecs_cluster'
    test_params['container_instance_arn'] = 'arn:aws:ecs:us-west-2:631042910881:container-instance/sandbox-dev-0-ecs_cluster/d714986f2e4e4434940b873c50e87075'
    test_params['subject'] = 'Draining instance {}'.format(
        test_params['container_instance_arn'].split('/')[-1])
    test_params['topic_arn'] = 'arn:aws:sns:us-west-2:631042910881:sandbox-dev-0-ecs-cluster-LifeCycleHook'
    return test_params

@pytest.fixture
def sns_message_id():
    """
    event_message fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/sns_message.json')
    with open(path) as sns_message_file:
        return json.load(sns_message_file)

@pytest.fixture
def event_message():
    """
    event_message fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/message.json')
    with open(path) as message_file:
        return json.load(message_file)


@pytest.fixture
def update_container_instances_state_response():
    """
    update_container_instances_state_response fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/update_container_instances_state.json')
    with open(path) as update_container_instances_state_file:
        return json.load(update_container_instances_state_file)


@pytest.fixture
def list_container_instances_response():
    """
    list_container_instances_response fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/list_container_instances.json')
    with open(path) as list_container_instances_file:
        return json.load(list_container_instances_file)


@pytest.fixture
def describe_container_instances_response():
    """
    describe_container_instances_response fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/describe_container_instances.json')
    with open(path) as describe_container_instances_file:
        return json.load(describe_container_instances_file)


@pytest.fixture
def list_tasks_response():
    """
    list_tasks_response fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/list_tasks.json')
    with open(path) as list_tasks_file:
        return json.load(list_tasks_file)


@pytest.fixture
def list_clusters_response():
    """
    list_clusters_response fixture
    """
    path = os.path.join(os.path.dirname(__file__), 'fixtures/list_clusters.json')
    with open(path) as list_clusters_file:
        return json.load(list_clusters_file)


def test_list_running_tasks(list_tasks_response, test_params):
    """
    Method tests list_running_tasks
    :param list_tasks_response:
    :return:
    """
    with Stubber(drain.ecs_client) as ecs_client_stubber:
        # assert that the request is made to list-tasks method
        # list-tasks request params
        list_tasks_params = {
            'cluster': test_params['cluster_arn'],
            'containerInstance': test_params['container_instance_arn'],
            'desiredStatus': 'RUNNING'
        }
        ecs_client_stubber.add_response(
            'list_tasks',
            list_tasks_response,
            list_tasks_params
        )
        task_arns = drain.list_running_tasks(
            test_params['cluster_arn'], test_params['container_instance_arn'])
        assert len(task_arns) == 3


@mock.patch('ecsdrain.drain.drain_instance')
def test_get_ecs_ids(drain_instance_patch, list_clusters_response, list_container_instances_response, describe_container_instances_response, test_params):
    """
    Method tests get_ecs_ids
    :param drain_instance_patch:
    :param list_clusters_response:
    :param list_container_instances_response:
    :param describe_container_instances_response:
    :return:
    """
    with Stubber(drain.ecs_client) as ecs_client_stubber:
        
        # Stubbing list-clusters API call
        ecs_client_stubber.add_response(
            'list_clusters',
            list_clusters_response
        )
        # Stubbing list-container-instances API call
        # list-container-instances request params
        list_container_instances_params = {
            'cluster': test_params['cluster_arn']
        }
        ecs_client_stubber.add_response(
            'list_container_instances',
            list_container_instances_response,
            list_container_instances_params
        )
        # Stubbing describe-container-instances API call
        # describe-container-instances request params
        describe_container_instances_params = {
            'cluster': test_params['cluster_arn'],
            'containerInstances': list_container_instances_response['containerInstanceArns']
        }
        ecs_client_stubber.add_response(
            'describe_container_instances',
            describe_container_instances_response,
            describe_container_instances_params
        )
        cluster, container_instance = drain.get_ecs_ids(
            test_params['ec2_instance_id'])
        drain_instance_patch.assert_called_once_with(
            test_params['cluster_arn'], test_params['container_instance_arn'])
        assert cluster == test_params['cluster_arn']
        assert container_instance == test_params['container_instance_arn']


def test_drain_instance(update_container_instances_state_response, test_params):
    """
    Method tests drain_instance
    :param update_container_instances_state_response:
    :return:
    """
    with Stubber(drain.ecs_client) as ecs_client_stubber:
        # Stubbing update-container-instances-state API call
        # update-container-instances-state request params
        update_container_instances_state_params = {
            'cluster': test_params['cluster_arn'],
            'containerInstances': [test_params['container_instance_arn']],
            'status': 'DRAINING'
        }
        ecs_client_stubber.add_response(
            'update_container_instances_state',
            update_container_instances_state_response,
            update_container_instances_state_params
        )
        drain.drain_instance(
            test_params['cluster_arn'], test_params['container_instance_arn'])


def test_publish_to_sns(event_message, sns_message_id, test_params):
    """
    Method tests publish_to_sns
    :param event_message,
    :param subject,
    :param topic_arn
    :return:
    """
    with Stubber(drain.sns_client) as sns_client_stubber:
        # Stubbing update-container-instances-state API call
        # update-container-instances-state request params
        publish_params = {
            'TopicArn':test_params['topic_arn'],
            'Message': json.dumps(event_message),
            'Subject': test_params['subject']
        }
        sns_client_stubber.add_response(
            'publish',
            sns_message_id,
            publish_params
        )
        drain.publish_to_sns(
            event_message, test_params['subject'], test_params['topic_arn'])
