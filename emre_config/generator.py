import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class InstanceClass(Enum):
    # m4: bool = False  # why?
    M5 = "m5"
    M5A = "m5a"
    M6A = "m6a"
    # m6i:  # Reason: jdk17: JDK-8321599 Data loss in AVX3 Base64 decoding
    M6G = "m6g"
    # m7a:  # Reason: jdk17: JDK-8321599 Data loss in AVX3 Base64 decoding
    # m7i:  # Reason: jdk17: JDK-8321599 Data loss in AVX3 Base64 decoding
    M7G = "m7g"


@dataclass
class ConfigGenerator:
    is_master_spot: bool
    is_core_spot: bool
    is_task_spot: bool
    task_instance_size: int  # target
    worker_cores: int  # target
    # normally not touched
    core_instance_size: int = field(default=1, init=False)
    core_instance_count: int = field(default=1, init=False)
    # calculated
    core_instance_cores: int = field(init=False)
    task_instance_cores: int = field(init=False)
    task_instance_count: int = field(init=False)

    def __post_init__(self):
        self.core_instance_cores = self._worker_instance_cores(
            True, self.core_instance_size
        )
        self.task_instance_cores = self._worker_instance_cores(
            False, self.task_instance_size
        )
        self.task_instance_count = math.ceil(
            (self.worker_cores - self.core_instance_count * self.core_instance_cores)
            / self.task_instance_cores
        )

    def instance_fleet_master(self) -> dict:
        return dict(
            InstanceFleetType="MASTER",
            TargetOnDemandCapacity=1 if not self.is_master_spot else 0,
            TargetSpotCapacity=1 if self.is_master_spot else 0,
            InstanceTypeConfigs=[
                dict(
                    InstanceType=f"{instance_class}.xlarge",
                    EbsConfiguration=dict(
                        EbsBlockDeviceConfigs=[
                            dict(
                                VolumeSpecification=dict(
                                    VolumeType="gp3",
                                    SizeInGB=32,
                                ),
                                VolumesPerInstance=1,
                            )
                        ],
                    ),
                )
                for instance_class in [ic.value for ic in InstanceClass]
            ],
        )

    def instance_fleet_worker(
        self,
        core: bool,
        launch_specifications: dict,
    ) -> dict:
        spot: bool = self.is_core_spot if core else self.is_task_spot
        instance_count: int = (
            self.core_instance_count if core else self.task_instance_count
        )
        instance_cores: int = (
            self.core_instance_cores if core else self.task_instance_cores
        )
        instance_size: int = (
            self.core_instance_size if core else self.task_instance_size
        )
        return dict(
            InstanceFleetType="CORE" if core else "TASK",
            TargetOnDemandCapacity=instance_count * instance_cores if not spot else 0,
            TargetSpotCapacity=instance_count * instance_cores if spot else 0,
            InstanceTypeConfigs=[
                self._worker_instance_configuration(
                    instance_class, instance_size, instance_cores
                )
                for instance_class in [ic.value for ic in InstanceClass]
            ],
            LaunchSpecifications=launch_specifications,
        )

    def get_configurations(self) -> List[dict]:
        return [
            dict(
                Classification="yarn-site",
                Properties={
                    # seems to be an upper bound for the max capability reported from nodes
                    "yarn.scheduler.maximum-allocation-vcores": f"{2 ** 31 - 1}",
                    "yarn.scheduler.maximum-allocation-mb": f"{2 ** 31 - 1}",
                    # dynamic allocation: no deallocation => no shuffle service
                    "yarn.nodemanager.aux-services": "",
                },
            ),
            dict(
                Classification="spark-defaults",
                Properties={
                    # AWS specific: heterogeneous executors
                    # executors 1-4 cores, 4 - 16 GiB
                    "spark.yarn.heterogeneousExecutors.enabled": "true",
                    "spark.executor.maxCores": "4",
                    "spark.executor.cores": "1",
                    "spark.executor.memory": "3449m",
                    "spark.executor.memoryOverhead": "647m",
                    # dynamic allocation: no deallocation => no shuffle service
                    "spark.dynamicAllocation.enabled": "true",
                    "spark.dynamicAllocation.minExecutors": "1024",
                    "spark.dynamicAllocation.shuffleTracking.enabled": "true",
                    "spark.shuffle.service.enabled": "false",
                    # spot interruptions
                    "spark.decommission.enabled": "true",
                    "spark.storage.decommission.enabled": "true",
                    # glue catalog
                    "spark.hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory",
                    "spark.hadoop.aws.glue.catalog.separator": "/",
                    # TODO parallelism
                    "spark.default.parallelism": str(
                        self.core_instance_count * self.core_instance_cores
                        + self.task_instance_count * self.task_instance_cores
                    ),
                    "spark.sql.shuffle.partitions": str(
                        self.core_instance_count * self.core_instance_cores
                        + self.task_instance_count * self.task_instance_cores
                    ),
                },
            ),
            dict(
                Classification="spark-log4j2",
                Properties={
                    "logger.TaskSetManager.name": "org.apache.spark.scheduler.TaskSetManager",
                    "logger.TaskSetManager.level": "WARN",
                },
            ),
        ]

    @staticmethod
    def _worker_instance_cores(core_type: bool, instance_size: int) -> int:
        """
        Calculate the number of usable cores for a worker instance.

        Args:
            core_type (bool): Whether the instance is a EMR core (type).
            instance_size (int): The size of the instance (like 4 for 4xlarge).

        Returns:
            int: The number of usable cores.

        """
        cores = instance_size * 4
        reserved_cores = 2 if core_type and instance_size > 1 else 1
        usable_cores = cores - reserved_cores
        return usable_cores

    @classmethod
    def _worker_instance_configuration(
        cls, instance_class: str, instance_size: int, instance_cores: int
    ) -> dict:
        """
        Generate the configuration for a worker instance.

        Args:
            instance_class (str): The class of the instance.
            instance_size (int): The size of the instance (like 4 for 4xlarge).
            instance_cores (int): The number of cores for the instance.

        Returns:
            dict: The configuration for the worker instance.
        """
        instance_type = (
            f"{instance_class}.{instance_size if instance_size > 1 else ''}xlarge"
        )
        volume_count, volume_size = cls._default_instance_storage(instance_size)
        return dict(
            InstanceType=instance_type,
            WeightedCapacity=instance_cores,
            EbsConfiguration=dict(
                EbsBlockDeviceConfigs=[
                    dict(
                        VolumeSpecification=dict(
                            VolumeType="gp3",
                            SizeInGB=volume_size,
                        ),
                        VolumesPerInstance=volume_count,
                    ),
                ],
            ),
            Configurations=[
                dict(
                    Classification="yarn-site",
                    Properties={
                        "yarn.nodemanager.resource.cpu-vcores": f"{instance_cores}",
                        "yarn.nodemanager.resource.memory-mb": f"{instance_cores * 4 * 1024}",
                    },
                ),
            ],
        )

    @staticmethod
    def _default_instance_storage(instance_size: int) -> tuple[int, int]:
        """
        Calculate the default instance storage configuration based on the given instance size.

        Args:
            instance_size (int): The size of the instance  (like 4 for 4xlarge).

        Returns:
            tuple[int, int]: A tuple containing the number of volumes and the size of each volume.
        """
        target_size = instance_size * 64
        volume_count = 4
        volume_size = math.ceil(target_size / volume_count)
        if volume_size < 32:
            volume_size = 32
            volume_count = math.ceil(target_size / volume_size)
        return volume_count, volume_size


# TODO: usage ?
def hdfs_replication_level(number_of_core_nodes: int) -> int:
    return 1 if number_of_core_nodes < 4 else (2 if number_of_core_nodes < 10 else 3)
