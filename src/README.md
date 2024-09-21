## prerequisite
`helm install spark-operator spark-operator/spark-operator --namespace spark-operator --set "sparkJobNamespaces={spark-operator}" --create-namespace --set webhook.enable=true`安裝好spark-operator
## 使用方式
1. `python pipeline/kubeflow_pipeline.py`編譯出pipeline的yaml檔案
2. `kubectl apply -f rbac/pipeline-runner-cluster-rbac.yaml`讓pipeline SA有權限可以部屬sparkapplication
3. `kubectl apply -f pvc.yaml`
4. 上傳pipeline到kubeflow中

___

## TODO
- [x] pipeline sdkv1 to sdkv2
- [ ] complete volume mount for data processing with NFS
- [ ] fullpipeline with pyspark-data-processing+model training in kfpv2

