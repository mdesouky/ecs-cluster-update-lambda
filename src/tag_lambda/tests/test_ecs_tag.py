"""
Unit Tests for Tag Lambda function.
"""
import json
import os
from mock import patch
from botocore.stub import Stubber, ANY
from ecstag import tag




ECS_STACK_NAME = 'sandbox-dev-0-ecs-cluster'
instance_ids = []


def describe_auto_scaling_groups_response():
    """
    list_clusters_response fixture
    """
    path = os.path.join(os.path.dirname(__file__),
                        'fixtures/autoscaling_groups.json')
    with open(path) as describe_auto_scaling_groups_file:
        return json.load(describe_auto_scaling_groups_file)




def test_get_instance_ids_by_tag():
    """
    Method tests handler
    :param logger_patch:
    :return:
    """
    with Stubber(tag.asg_client) as asg_client_stubber:
        # assert that the request is made to describe_images method
        asg_client_stubber.add_response(
            'describe_auto_scaling_groups',
            describe_auto_scaling_groups_response()
        )
        # describe_auto_scaling_groups response returning two ASG's

        instance_ids = tag.get_instance_ids_by_tag(ECS_STACK_NAME)
        assert len(instance_ids) == 2
        

def test_set_drain_tag():
    """
    Method tests set_drain_tag
    :param 
    :return:
    """
    with Stubber(tag.ec2_client) as ec2_client_stubber:
        # Stubbing create-tags API call
        # create-tags request params
        create_tags_params = {
            'DryRun':False,
            'Resources': instance_ids,
            'Tags': [{'Key': 'drain', 'Value': 'true'}]
                

        }
        
        ec2_client_stubber.add_response(
            'create_tags',
            '',
            create_tags_params
        )

        tag.set_drain_tag(instance_ids, True)

    
