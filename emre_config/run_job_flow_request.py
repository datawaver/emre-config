from ast import Dict
from typing import Any
from emre_config.ConfigGenerator import (
    ConfigGenerator,
)
from emre_config.parameters import AWSParameters, TargetFlowParameters

EMR_IDLE_TIMEOUT_IN_SECONDS = 30 * 60


def run_job_flow_request(target: TargetFlowParameters, aws: AWSParameters) -> dict:
    config = ConfigGenerator(
        is_master_spot=target.master_spot,
        is_core_spot=target.core_spot,
        is_task_spot=target.task_spot,
        task_instance_size=target.task_instance_size,
        worker_cores=target.target_worker_cores,
    )

    result: dict[str, Any] = dict(
        Name=target.cluster_name,
        ReleaseLabel="emr-7.0.0",
        Applications=[
            {
                "Name": "Spark",
            },
            {
                "Name": "AmazonCloudWatchAgent",
            },
        ],
        ServiceRole="EMR_DefaultRole",
        JobFlowRole="EMR_EC2_DefaultRole",
        Tags=aws.tags,
        LogUri=aws.log_uri,
        EbsRootVolumeSize=15,  # minimum
        Instances=dict(
            KeepJobFlowAliveWhenNoSteps=True,
            TerminationProtected=False,
            Ec2SubnetIds=aws.ec2_subnet_ids,
            EmrManagedMasterSecurityGroup=aws.security_groups["EmrManagedMaster"],
            EmrManagedSlaveSecurityGroup=aws.security_groups["EmrManagedSlave"],
            ServiceAccessSecurityGroup=aws.security_groups["ServiceAccess"],
            InstanceFleets=[
                config.instance_fleet_master(),
                config.instance_fleet_worker(
                    True,
                    launch_specifications=aws.launch_specifications,
                ),
                config.instance_fleet_worker(
                    False,
                    launch_specifications=aws.launch_specifications,
                ),
            ],
        ),
        Configurations=config.get_configurations(),
        AutoTerminationPolicy=dict(
            IdleTimeout=EMR_IDLE_TIMEOUT_IN_SECONDS,
        ),
    )
    return remove_none_values(result)


def remove_none_values(d: dict) -> dict:
    if not isinstance(d, dict):
        return d
    return {k: remove_none_values(v) for k, v in d.items() if v is not None}
