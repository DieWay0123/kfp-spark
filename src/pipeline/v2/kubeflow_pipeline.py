import json
import time

from yaml import YAMLObject
import yaml

import kfp.components as comp
import kfp.dsl as dsl
from kfp.dsl import container_component, ContainerSpec, Input, Output, InputPath, OutputPath, Artifact, Dataset
from kfp import kubernetes


def get_spark_job_definition(sparkApplication_NS, sparkApplication_SA, dataset_path):
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
    spark_job_manifest["spec"]["driver"]["env"][0]["datasetPath"] = spark_job_manifest["spec"]["driver"]["env"][0]["datasetPath"].format(datasetPath=dataset_path)
    spark_job_manifest["spec"]["executor"]["env"][0]["datasetPath"] = spark_job_manifest["spec"]["executor"]["env"][0]["datasetPath"].format(datasetPath=dataset_path)
    return spark_job_manifest

#Get and concat dataset
@dsl.component(
  base_image="dieway/get-dataset-nfs-server:diabetes",
  packages_to_install=["python-dotenv==1.0.1", "pandas==2.2.2", "numpy==2.0.0"]
)
def load_raw_datasets_from_nfs(
  diabetes_dataset: Output[Dataset]
):
  import os
  import shutil
  import pandas as pd
  from dotenv import load_dotenv, dotenv_values
  
  config = dotenv_values(".env")
  
  nfs_server = config["NFS_SERVER"]
  mount_point = config["MOUNT_POINT"]
  pwd = config["PASSWORD"]

  # mount nfs
  if not os.path.exists(mount_point):
    os.makedirs(mount_point)

  os.system(f"echo {pwd} | sudo -S mount -t nfs {nfs_server} {mount_point}")
  
  # copy file
  source_file = config["SOURCE_FILE"]
  destination_file = config["DESTINATION_FILE"]

  # 複製文件
  while not os.path.exists(source_file):
    print(f"file {source_file} not found")

  shutil.copyfile(source_file, destination_file)

  os.system(f"sudo umount {mount_point}")
  #os.system(f"chmod -R 777 {destination_file}")
  os.system(f"echo copy datasets from nfs-servre DONE!")
  
  # data passing in pipeline
  dataset_pd = pd.read_csv(destination_file)
  dataset_pd.to_csv(diabetes_dataset.path)

@dsl.component(
  base_image="python:3.9"
)
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

    load_raw_data__from_nfs_task = load_raw_datasets_from_nfs()
    # Load the kubernetes apply component
    dataset_path = load_raw_data__from_nfs_task.outputs['diabetes_dataset']
    spark_job_definition = get_spark_job_definition(sparkApplication_NS=sparkApplication_NS, sparkApplication_SA=sparkApplication_SA, dataset_path=dataset_path)
    k8s_apply_op = comp.load_component_from_file("k8s-apply-component.yaml")
    # Execute the apply command
    spark_job_op = k8s_apply_op(object=json.dumps(spark_job_definition), dataset=dataset_path)

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
