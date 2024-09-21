#!/bin/bash

# Step 1: Edit the ClusterRole to add the label
kubectl get clusterrole spark-operator -o yaml > spark-operator.yaml
sed -i '/labels/a\ \ \ \ rbac.authorization.kubeflow.org/aggregate-to-kubeflow-edit: "true"' spark-operator.yaml
kubectl apply -f spark-operator.yaml

# Step 2: Apply the ClusterRoleBinding
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
