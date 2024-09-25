#!/bin/bash

kubectl get clusterrole spark-operator -o yaml > spark-operator.yaml
sed -i '/labels/a\ \ \ \ rbac.authorization.kubeflow.org/aggregate-to-kubeflow-edit: "true"' spark-operator.yaml
kubectl apply -f spark-operator.yaml

cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: default-editor
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubeflow-edit
subjects:
- kind: ServiceAccount
  name: default-editor
  namespace: kubeflow-user-example-com
EOF

echo "ClusterRole and ClusterRoleBinding have been updated successfully."
