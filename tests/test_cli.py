import json
from click.testing import CliRunner
from emre_config.cli import cli
import os

def test_cli():
    runner = CliRunner()
    aws_config_path = os.path.join(os.path.dirname(__file__), "example_input_aws_config.json")
    result = runner.invoke(cli, ["--aws-config", aws_config_path])
    assert result.exit_code == 0
    assert json.loads(result.output) == json.load(open("tests/example_resulting_runner_config.json"))