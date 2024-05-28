import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class TargetFlowParameters:
    cluster_name: str
    master_spot: bool
    core_spot: bool
    task_spot: bool
    task_instance_size: int
    target_worker_cores: int


@dataclass
class AWSParameters:
    ec2_subnet_ids: List[str]
    security_group: Dict[str, str]
    log_uri: str
    tags: List[Dict[str, str]]
    launch_specifications: Dict[str, str]

    @staticmethod
    def load(file_path: Path) -> "AWSParameters":
        with open(file_path) as config_file:
            config = json.load(config_file)
            return AWSParameters(
                ec2_subnet_ids=config["ec2_subnet_ids"],
                security_group=config["security_group"],
                log_uri=config["log_uri"],
                tags=config["tags"],
                launch_specifications=config["launch_specifications"],
            )
