import json
import time
import yaml

import kfp.components as comp
import kfp.dsl as dsl

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


def print_msg(msg: str) -> str:
    print(msg)
    return msg


@dsl.graph_component  # Graph component decorator is used to annotate recursive functions
def graph_component_spark_app_status(input_application_name):
    k8s_get_op = comp.load_component_from_file("k8s-get-component.yaml")
    check_spark_application_status_op = k8s_get_op(
        name=input_application_name,
        kind=SPARK_APPLICATION_KIND
    )
    # Remove cache
    check_spark_application_status_op.execution_options.caching_strategy.max_cache_staleness = "P0D"

    time.sleep(5)
    with dsl.Condition(check_spark_application_status_op.outputs["applicationstate"] != SPARK_COMPLETED_STATE):
        graph_component_spark_app_status(check_spark_application_status_op.outputs["name"])

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

    # Load the kubernetes apply component
    k8s_apply_op = comp.load_component_from_file("k8s-apply-component.yaml")

    # Execute the apply command
    spark_job_op = k8s_apply_op(object=json.dumps(spark_job_definition))

    # Fetch spark job name
    spark_job_name = spark_job_op.outputs["name"]
    
    spark_job_op.execution_options.caching_strategy.max_cache_staleness = "P0D"

    print_op = comp.func_to_container_op(
      print_msg,
      base_image="python:3.9",
    )

    print_message = print_op(f"Job {spark_job_name} is completed.")
    #print_message.after(spark_application_status_op)
    print_message.execution_options.caching_strategy.max_cache_staleness = "P0D"


if __name__ == "__main__":
    # Compile the pipeline
    import kfp.compiler as compiler
    import logging
    logging.basicConfig(level=logging.INFO)
    pipeline_func = spark_job_pipeline
    pipeline_filename = pipeline_func.__name__ + ".yaml"
    compiler.Compiler().compile(pipeline_func, pipeline_filename)
    logging.info(f"Generated pipeline file: {pipeline_filename}.")
