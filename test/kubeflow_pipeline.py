import json
import time
import yaml

import kfp
from kfp import dsl
from kfp.dsl import Input, Output, Artifact, Dataset, InputPath, OutputPath
import kfp.components as comp

SPARK_COMPLETED_STATE = "COMPLETED"
SPARK_APPLICATION_KIND = "sparkapplications"

#DONE
def get_spark_job_definition():
    """
    Read Spark Operator job manifest file and return the corresponding dictionary and
    add some randomness in the job name
    :return: dictionary defining the spark job
    """
    # Read manifest file
    with open("spark-job-python.yaml", "r") as stream:
        spark_job_manifest = yaml.safe_load(stream)

    # Add epoch time in the job name(Random)
    epoch = int(time.time())
    spark_job_manifest["metadata"]["name"] = spark_job_manifest["metadata"]["name"].format(epoch=epoch)

    return spark_job_manifest

@dsl.container_component
def print_op(msg: String):
    return ContainerSpec(
        name="Print message.",
        image="alpine:latest",
        command=["echo", msg]
    )

'''
def print_op(msg):
    """
    Op to print a message.
    """
    return dsl.ContainerOp(
        name="Print message.",
        image="alpine:3.6",
        command=["echo", msg],
    )


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
'''

'''
@dsl.component(
        base_image='python:3.9'
)
def load_kubectl_apply_SparkApplication(SparkApplication_YAML: InputPath('JsonObject'), twe :OutputPath('YAML')): #type: ignore
    test='a'
'''

@dsl.component(
    base_image='bitnami/kubectl:1.29.8',
    packages_to_install=['yaml']
)
def kubectl_apply_op_test(SparkApplication_YAML: InputPath('String') ): # type: ignore
    import json
    import yaml
    k8s_apply_op = comp.load_component_from_file("k8s-apply-component.yaml")
    k8s_apply_YAML =  yaml.safe_load(k8s_apply_op)
    with open(SparkApplication_YAML.path, 'w') as f:
        yaml.dump(k8s_apply_YAML, f)

@dsl.component(
    base_image='python:3.9'
)
def create_artifact(
    data: str,
    output_artifact: Output[Artifact],
):
    with open(output_artifact.path, 'w') as f:
        f.write(data)


@dsl.pipeline(
    name="Spark Operator job pipeline",
    description="Spark Operator job pipeline"
)
def spark_job_pipeline():

    #1
    # Load spark job manifest
    # 從SparkApplication的template取得SparkApplication的yaml到pipeline中
    spark_job_definition = get_spark_job_definition()

    #2
    # Load the kubernetes apply component
    # 載入kubectl apply SparkApplication的template
    k8s_apply_op = comp.load_component_from_file("k8s-apply-component.yaml")


    #k8s_apply_json_test = json.dumps(yaml.safe_load(k8s_apply_op.component_yaml))
    #print(k8s_apply_json_test['metadata'])
    #k8s_apply_op(object=k8s_apply_json_test)
    #3
    # Execute the apply command
    # component送出kubectl apply SparkApplication的指令
    k8s_apply_json = json.dumps(spark_job_definition)
    k8s_apply_artifact_task = create_artifact(data=k8s_apply_json)
#    spark_job_op = k8s_apply_op(object)
    #k8s_apply_json = json.dumps(spark_job_definition)
    spark_job_op = k8s_apply_op(object=k8s_apply_artifact_task.outputs['output_artifact'])
    #print(k8s_apply_json)
'''
    #4
    # Fetch spark job name
    spark_job_name = spark_job_op.outputs["name"]

    #5
    # Remove cache for the apply operator
    spark_job_op.execution_options.caching_strategy.max_cache_staleness = "P0D"
'''

'''
    spark_application_status_op = graph_component_spark_app_status(spark_job_op.outputs["name"])
    spark_application_status_op.after(spark_job_op)

    print_message = print_op(f"Job {spark_job_name} is completed.")
    print_message.after(spark_application_status_op)
    print_message.execution_options.caching_strategy.max_cache_staleness = "P0D"
'''

#DONE
if __name__ == "__main__":
    # Compile the pipeline
    import kfp.compiler as compiler
    import logging
    logging.basicConfig(level=logging.INFO)
    pipeline_func = spark_job_pipeline
    pipeline_filename = "Spark_Operator_job_pipeline.yaml"
    compiler.Compiler().compile(spark_job_pipeline, 'spark_job_pipeline.yaml')
    logging.info(f"Generated pipeline file: {pipeline_filename}.")