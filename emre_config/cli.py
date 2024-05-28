import json
import click
from emre_config.run_job_flow_request import run_job_flow_request
from emre_config.parameters import TargetFlowParameters, AWSParameters


@click.command()
@click.option("--cluster-name", default="template_1", help="Name of the EMR cluster")
@click.option(
    "--master-spot",
    default=True,
    type=bool,
    help="Whether to use spot instance for master node",
)
@click.option(
    "--core-spot",
    default=True,
    type=bool,
    help="Whether to use spot instances for core nodes",
)
@click.option(
    "--task-spot",
    default=True,
    type=bool,
    help="Whether to use spot instances for task nodes",
)
@click.option(
    "--task-instances", default=16, type=int, help="Size of the task instance"
)
@click.option(
    "--target-worker-cores",
    default=4,
    type=int,
    help="Number of cores for the target worker",
)
@click.option(
    "--aws-config",
    default="aws_config.json",
    type=click.Path(exists=True),
    help="Path to the AWS environment configuration file",
)
def cli(
    cluster_name,
    master_spot,
    core_spot,
    task_spot,
    task_instances,
    target_worker_cores,
    aws_config,
):
    target_job_flow_parameters: TargetFlowParameters = TargetFlowParameters(
        cluster_name=cluster_name,
        master_spot=master_spot,
        core_spot=core_spot,
        task_spot=task_spot,
        task_instance_size=task_instances,
        target_worker_cores=target_worker_cores,
    )
    request = run_job_flow_request(
        target_job_flow_parameters, aws=AWSParameters.load(aws_config)
    )
    print(json.dumps(request))


if __name__ == "__main__":
    cli()
