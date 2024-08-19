import json

import time

import yaml



import kfp

from kfp import dsl

from kfp.dsl import Input, Output, Artifact, Dataset, InputPath, OutputPath

from kfp.dsl import ContainerSpec

from kfp import local

import kfp.components as comp



local.init(runner=local.SubprocessRunner(use_venv=False))



@dsl.component(

  base_image='python:3.9',

)

def kubectl_apply_local(file_path: str):

  import subprocess

  import json

  import time

  result = subprocess.run(['kubectl', 'apply', '-f', file_path], capture_output=True, text=True)

  if result.returncode != 0:

    raise Exception(f"Error applying kubectl: {result.stderr}")

  print(result.stdout)



@dsl.component(

    base_image='python:3.9'

)
#for test
def create_artifact(

    data: str,

    output_artifact: Output[Artifact],

):

    with open(output_artifact.path, 'w') as f:

        f.write(data)



@dsl.pipeline(

  name='test kubectl apply local',

  description='rt'

)

def kubectl_apply_pipeline(file_path: str):

  kubectl_apply_task = kubectl_apply_local(file_path=file_path)

  create_artifact_task = create_artifact(data="Goodbye, World!")



if __name__ ==  '__main__':
  kfp.compiler.Compiler().compile(kubectl_apply_pipeline, 'kubectl_apply_pipeline_test.yaml')
  kubectl_apply_pipeline(file_path='/home/k8master/Documents/sparkTest/test/spark-job-process-10kdataset.yaml')
