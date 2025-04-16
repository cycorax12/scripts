from kubernetes import client
from kubernetes.client import Configuration, ApiClient
import oracledb
from datetime import datetime
import urllib3

# -------------------------------
# Config
# -------------------------------
CLUSTER_API = "https://api.your-cluster.com:6443"
BEARER_TOKEN = "your_token"
NAMESPACE = "your-namespace"
VERIFY_SSL = False

ORACLE_USER = "db_user"
ORACLE_PASS = "db_pass"
ORACLE_DSN = "host:port/service"

# -------------------------------
# Setup Kubernetes API client
# -------------------------------
urllib3.disable_warnings()

config = Configuration()
config.host = CLUSTER_API
config.verify_ssl = VERIFY_SSL
config.api_key = {"authorization": "Bearer " + BEARER_TOKEN}
config.api_key_prefix = {"authorization": "Bearer"}
client.Configuration.set_default(config)
api_client = ApiClient(config)

core_v1 = client.CoreV1Api(api_client)
apps_v1 = client.AppsV1Api(api_client)
custom = client.CustomObjectsApi(api_client)

# -------------------------------
# Unit Conversion
# -------------------------------
def parse_cpu(cpu_str):
    if cpu_str.endswith("n"):
        return float(cpu_str[:-1]) / 1e6
    elif cpu_str.endswith("u"):
        return float(cpu_str[:-1]) / 1e3
    elif cpu_str.endswith("m"):
        return float(cpu_str[:-1])
    else:
        return float(cpu_str) * 1000

def parse_memory(mem_str):
    mem_str = mem_str.strip()
    unit_multipliers = {
        "Ki": 1024, "Mi": 1024**2, "Gi": 1024**3,
        "Ti": 1024**4, "Pi": 1024**5, "Ei": 1024**6,
        "KiB": 1000, "MiB": 1000**2, "GiB": 1000**3,
        "TiB": 1000**4, "PiB": 1000**5, "EiB": 1000**6,
    }
    for unit in sorted(unit_multipliers.keys(), key=len, reverse=True):
        if mem_str.endswith(unit):
            return float(mem_str[:-len(unit)]) * unit_multipliers[unit]
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
# Collect & Store Metrics
# -------------------------------
def collect_metrics_and_store():
    timestamp = datetime.now()
    results = custom.list_namespaced_custom_object(
        group="metrics.k8s.io", version="v1beta1", plural="pods", namespace=NAMESPACE
    )

    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
    cur = conn.cursor()

    for pod_metrics in results['items']:
        pod_name = pod_metrics['metadata']['name']
        namespace = pod_metrics['metadata']['namespace']

        try:
            cpu_total = 0
            mem_total = 0
            cpu_req = 0
            cpu_lim = 0
            mem_req = 0
            mem_lim = 0

            # Usage
            for container in pod_metrics['containers']:
                cpu_total += parse_cpu(container['usage']['cpu'])
                mem_total += parse_memory(container['usage']['memory'])

            # Resource requests/limits
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            deployment = get_deployment_for_pod(pod.metadata)

            for container in pod.spec.containers:
                resources = container.resources

                if resources.requests:
                    cpu_req += parse_cpu(resources.requests.get("cpu", "0"))
                    mem_req += parse_memory(resources.requests.get("memory", "0"))

                if resources.limits:
                    cpu_lim += parse_cpu(resources.limits.get("cpu", "0"))
                    mem_lim += parse_memory(resources.limits.get("memory", "0"))

            cur.execute("""
                INSERT INTO pod_metrics (
                    pod_name, deployment_name, namespace,
                    cpu_millicores, memory_bytes,
                    cpu_request, cpu_limit,
                    memory_request, memory_limit,
                    timestamp
                )
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
            """, (
                pod_name,
                deployment,
                namespace,
                round(cpu_total, 2),
                round(mem_total, 2),
                round(cpu_req, 2),
                round(cpu_lim, 2),
                round(mem_req, 2),
                round(mem_lim, 2),
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
