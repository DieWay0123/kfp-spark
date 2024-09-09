import json
import time

from yaml import YAMLObject
import yaml

import kfp.components as comp
import kfp.dsl as dsl
from kfp.dsl import container_component, ContainerSpec, Input, Output, InputPath, OutputPath, Artifact

SPARK_COMPLETED_STATE = "COMPLETED"
SPARK_APPLICATION_KIND = "sparkapplications"


def get_spark_job_definition(sparkApplication_NS, sparkApplication_SA):
    """
    Read Spark Operator job manifest file and return the corresponding dictionary and
    add some randomness in the job name
    :return: dictionary defining the spark job
    """
    # Read manifest file
    with open("spark-job-python-10kprocess.yaml", "r") as stream:
        spark_job_manifest = yaml.safe_load(stream)

    # Add epoch time in the job name
    epoch = int(time.time())
    spark_job_manifest["metadata"]["name"] = spark_job_manifest["metadata"]["name"].format(epoch=epoch)
    spark_job_manifest["metadata"]["namespace"] = spark_job_manifest["metadata"]["namespace"].format(NS=sparkApplication_NS)
    spark_job_manifest["spec"]["driver"]["serviceAccount"] = spark_job_manifest["spec"]["driver"]["serviceAccount"].format(SA=sparkApplication_SA)

    return spark_job_manifest

@dsl.component
def print_msg(msg: str) -> str:
    print(msg)
    return msg


@dsl.pipeline(
    name="Spark Operator job pipeline",
    description="Spark Operator job pipeline"
)
def spark_job_pipeline(
  sparkApplication_NS: str,
  sparkApplication_SA: str,
):

    # Load spark job manifest
    spark_job_definition = get_spark_job_definition(sparkApplication_NS=sparkApplication_NS, sparkApplication_SA=sparkApplication_SA)
    # spark_job_op = apply_sparkJob(sparkJob=yaml.dump(spark_job_definition))
    
    # Load the kubernetes apply component
    k8s_apply_op = comp.load_component_from_file("k8s-apply-component.yaml")

    # Execute the apply command
    spark_job_op = k8s_apply_op(object=json.dumps(spark_job_definition))

    # Fetch spark job name
    spark_job_name = spark_job_definition["metadata"]["name"]
    
    spark_job_op.set_caching_options(enable_caching=False)

    print_message = print_msg(msg=f"Job {spark_job_name} is completed.")
    #print_message.after(spark_application_status_op)
    print_message.set_caching_options(enable_caching=False)


if __name__ == "__main__":
    # Compile the pipeline
    import kfp.compiler as compiler
    import logging
    logging.basicConfig(level=logging.INFO)
    pipeline_func = spark_job_pipeline
    pipeline_filename = "sparkJobPipeline.yaml"
    compiler.Compiler().compile(pipeline_func, pipeline_filename)
    logging.info(f"Generated pipeline file: {pipeline_filename}.")
