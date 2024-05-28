from emre_config.generator import (
    ConfigGenerator,
)
from emre_config.parameters import AWSParameters, TargetFlowParameters


def run_job_flow_request(target: TargetFlowParameters, aws: AWSParameters) -> dict:

    config = ConfigGenerator(
        is_master_spot=target.master_spot,
        is_core_spot=target.core_spot,
        is_task_spot=target.task_spot,
        task_instance_size=target.task_instance_size,
        worker_cores=target.target_worker_cores,
    )

    return dict(
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
            EmrManagedMasterSecurityGroup=aws.security_group["EmrManagedMaster"],
            EmrManagedSlaveSecurityGroup=aws.security_group["EmrManagedSlave"],
            ServiceAccessSecurityGroup=aws.security_group["ServiceAccess"],
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
            IdleTimeout=30 * 60,
        ),
    )


# emr = boto3.client("emr")
# emr.run_job_flow(**run_job_flow_request)
