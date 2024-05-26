# EMRE Configuration

This tool will generate a configuration file for EMR clusters. It will generate a configuration file that can be used with `aws emr create-cluster` command.
You have to provide some AWS resources from your VPC. 

## Install

```bash
$ pipx install git+https://github.com/dataweaver/emre/config.git
```

Uninstall

```bash
$ pipx uninstall emre-config
```

## Usage

Provide a json file with the AWS resources you want to use. Here is an example:

```json
{
    "ec2_subnet_ids": [
        "subnet-aaaaaaaaaaaaaaaaa",
        "subnet-bbbbbbbbbbbbbbbbb"
    ],
    "security_group": {
        "EmrManagedMaster": "sg-00000000000000000",
        "EmrManagedSlave": "sg-11111111111111111",
        "ServiceAccess": "sg-aaaaaaaaaaaaaaaaa"
    },
    "log_uri": "s3://aws-logs-1234567890-eu-central-1/elasticmapreduce/",
    "tags": [
        {
            "Key": "project",
            "Value": "emre"
        }
    ],
    "launch_specifications": {
        "OnDemandSpecification": {
            "AllocationStrategy": "lowest-price"
        },
        "SpotSpecification": {
            "TimeoutDurationMinutes": 5,
            "TimeoutAction": "TERMINATE_CLUSTER",
            "AllocationStrategy": "price-capacity-optimized"
        }
    }
}
```
Assuming you have saved the file as `config.json`, you can run the command:

```bash
emre-config --aws-config config.json --task-instances 4 --cluster-name my-emre-cluster
```


## Developing

### Troubleshooting

If you get `botocore.exceptions.NoRegionError: You must specify a region.` error, you have to set the AWS region. Use `.env` or export it.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

