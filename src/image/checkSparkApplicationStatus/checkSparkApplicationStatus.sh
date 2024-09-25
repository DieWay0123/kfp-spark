#!/bin/bash

set -eux

SPARK_APPLICATION_NAME=$sparkapplication_name
NAMESPACE=$sparkapplication_namespace
SPARK_APPLICATION=$(kubectl get $SPARK_APPLICATION_NAME -n $NAMESPACE)
STATUS=$(echo $SPARK_APPLICATION | awk '{print $8}')

while true; do
  if [[ $STATUS == *COMPLETED* ]]; then
    echo "Sparkapplication finished!"
    break
  elif [[ $STATUS == *FAILED ]]; then
    echo "Sparkapplication failed!"
    break
  else
    echo "SParkapplication havent finished!"
  fi
  sleep 5
done

