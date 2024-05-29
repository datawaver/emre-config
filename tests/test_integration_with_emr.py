import pytest
import json
import boto3
from emre_config.cli import cli
import os
from click.testing import CliRunner


@pytest.mark.integration_test
def test_boto3():
    emr = boto3.client("emr")
    response = emr.list_clusters()
    assert "Clusters" in response


@pytest.mark.slow_integration_test
def test_integration_emr():
    runner = CliRunner()
    try:
        aws_config_path = os.path.join(os.path.dirname(__file__), "aws_config.json")
    except FileNotFoundError:
        print("Please manually create a file named aws_config.json in the tests directory to run this test.")
    result = runner.invoke(
        cli,
        ["--aws-config", aws_config_path, "--task-instances", "4", "--cluster-name", "emre-integration_test"],
    )
    assert result.exit_code == 0
    run_job_flow_request = json.loads(result.output)

    # Run the job flow to check if the configuration is correct
    client = boto3.client("emr")
    response = client.run_job_flow(**run_job_flow_request)
    cluster_id = response["ClusterArn"].split("/")[-1]
    waiter = client.get_waiter("cluster_running")
    try:
        waiter.wait(ClusterId=cluster_id, WaiterConfig={"Delay": 30 / 2, "MaxAttempts": 60 * 2})
    except Exception as e:
        print(client.describe_cluster(ClusterId=cluster_id)["Cluster"]["Status"])
        print(f"[bro tip] aws emr describe-cluster --cluster-id {cluster_id}")
        assert False, e
    client.terminate_job_flows(JobFlowIds=[cluster_id])  # save my money
