from kubernetes import client
from kubernetes.client import Configuration
import oracledb
from datetime import datetime
import urllib3

# -------------------------------
# OpenShift Cluster Auth Settings
# -------------------------------
CLUSTER_API = "https://api.your-cluster.example.com:6443"
BEARER_TOKEN = "your_long_service_account_or_user_token"
VERIFY_SSL = False  # Set to True and provide CA cert if needed
# CA_CERT_PATH = "/path/to/ca.crt"

# -------------------------------
# Oracle DB Settings
# -------------------------------
ORACLE_USER = "your_user"
ORACLE_PASS = "your_pass"
ORACLE_DSN = "your_db_host:1521/your_service"  # Example: 192.168.1.10:1521/ORCLPDB1

# -------------------------------
# Optional Namespace Filter
# -------------------------------
NAMESPACE_FILTER = None  # Example: "dev-namespace"

# -------------------------------
# Init Kubernetes Client
# -------------------------------
urllib3.disable_warnings()

k8s_config = Configuration()
k8s_config.host = CLUSTER_API
k8s_config.verify_ssl = VERIFY_SSL
k8s_config.api_key = {"authorization": "Bearer " + BEARER_TOKEN}
# k8s_config.ssl_ca_cert = CA_CERT_PATH  # If VERIFY_SSL is True

client.Configuration.set_default(k8s_config)
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
custom = client.CustomObjectsApi()

# -------------------------------
# Helper Functions
# -------------------------------

def parse_cpu(cpu_str):
    if cpu_str.endswith("n"):
        return float(cpu_str[:-1]) / 1e6  # nano → millicores
    elif cpu_str.endswith("u"):
        return float(cpu_str[:-1]) / 1000
    elif cpu_str.endswith("m"):
        return float(cpu_str[:-1])
    else:
        return float(cpu_str) * 1000  # cores → millicores

def parse_memory(mem_str):
    units = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3}
    for suffix, factor in units.items():
        if mem_str.endswith(suffix):
            return float(mem_str[:-len(suffix)]) * factor
    return float(mem_str)

def get_deployment_for_pod(pod_metadata):
    try:
        owner = pod_metadata.owner_references[0]
        if owner.kind == "ReplicaSet":
            rs = apps_v1.read_namespaced_replica_set(owner.name, pod_metadata.namespace)
            if rs.metadata.owner_references:
                return rs.metadata.owner_references[0].name
    except:
        return None
    return None

# -------------------------------
# Collect Metrics & Store in DB
# -------------------------------

def collect_metrics_and_store():
    timestamp = datetime.now()
    results = custom.list_cluster_custom_object(
        group="metrics.k8s.io", version="v1beta1", plural="pods"
    )

    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
    cur = conn.cursor()

    for pod_metrics in results['items']:
        namespace = pod_metrics['metadata']['namespace']
        pod_name = pod_metrics['metadata']['name']

        if NAMESPACE_FILTER and namespace != NAMESPACE_FILTER:
            continue

        try:
            cpu_total = 0
            mem_total = 0
            for container in pod_metrics['containers']:
                cpu_total += parse_cpu(container['usage']['cpu'])
                mem_total += parse_memory(container['usage']['memory'])

            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            deployment = get_deployment_for_pod(pod.metadata)

            cur.execute("""
                INSERT INTO pod_metrics (pod_name, deployment_name, namespace, cpu_millicores, memory_bytes, timestamp)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, (
                pod_name,
                deployment,
                namespace,
                round(cpu_total, 2),
                round(mem_total, 2),
                timestamp
            ))

        except Exception as e:
            print(f"[ERROR] {pod_name}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"[{timestamp}] Metrics collected and stored.")

# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    collect_metrics_and_store()
