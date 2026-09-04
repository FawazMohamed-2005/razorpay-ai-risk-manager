"""
Abuse-Ring Graph Sentinel
Builds and maintains a live NetworkX bipartite entity resolution graph connecting
Customers, Devices, IP Subnets, and VPAs to detect coordinated fraud syndicates.
Supports point-in-time subgraph filtering to prevent future data leakage.
"""

import os
import networkx as nx
import pandas as pd
import json

class GraphSentinel:
    def __init__(self):
        self.G = nx.Graph()
        
    def ingest_transaction(self, txn):
        cust = f"cust:{txn['customer_id']}"
        dev = f"dev:{txn['device_id']}"
        ip = f"ip:{txn['ip_address']}"
        ts = txn.get("timestamp")
        
        self.G.add_node(cust, type="customer", label=txn['customer_id'])
        self.G.add_node(dev, type="device", label=txn['device_id'])
        self.G.add_node(ip, type="ip", label=txn['ip_address'])
        
        self.G.add_edge(cust, dev, relationship="used_device", timestamp=ts)
        self.G.add_edge(cust, ip, relationship="used_ip", timestamp=ts)
        
        if txn.get("vpa") and str(txn["vpa"]).lower() != "nan" and str(txn["vpa"]).strip() != "":
            vpa = f"vpa:{txn['vpa']}"
            self.G.add_node(vpa, type="vpa", label=txn['vpa'])
            self.G.add_edge(cust, vpa, relationship="used_vpa", timestamp=ts)
            
    def populate_from_dataframe(self, df):
        for _, row in df.iterrows():
            self.ingest_transaction(row.to_dict())
            
    def inspect_entity_subgraph(self, entity_id, as_of_timestamp=None):
        """
        Extracts k-hop neighborhood around an entity.
        If as_of_timestamp is provided, edges occurring after as_of_timestamp are ignored.
        """
        target_node = None
        for prefix in ["cust:", "dev:", "ip:", "vpa:"]:
            if f"{prefix}{entity_id}" in self.G:
                target_node = f"{prefix}{entity_id}"
                break
                
        if not target_node:
            return {"entity_id": entity_id, "found": False, "nodes": [], "edges": [], "ring_metrics": {}}
            
        # Build filtered graph if as_of_timestamp is specified
        if as_of_timestamp:
            cutoff_dt = pd.to_datetime(as_of_timestamp)
            valid_edges = []
            for u, v, data in self.G.edges(data=True):
                edge_ts = data.get("timestamp")
                if edge_ts is None or pd.to_datetime(edge_ts) <= cutoff_dt:
                    valid_edges.append((u, v))
            working_G = self.G.edge_subgraph(valid_edges)
        else:
            working_G = self.G
            
        if target_node not in working_G:
            return {"entity_id": entity_id, "found": True, "nodes": [], "edges": [], "ring_metrics": {"linked_accounts_count": 1, "is_abuse_ring_pattern": False, "density": 0.0}}
            
        # 2-hop neighborhood
        sub_nodes = set([target_node])
        for n in working_G.neighbors(target_node):
            sub_nodes.add(n)
            for nn in working_G.neighbors(n):
                sub_nodes.add(nn)
                
        subgraph = working_G.subgraph(sub_nodes)
        
        # Analyze connected component
        component_customers = [n for n in sub_nodes if n.startswith("cust:")]
        component_devices = [n for n in sub_nodes if n.startswith("dev:")]
        component_ips = [n for n in sub_nodes if n.startswith("ip:")]
        component_vpas = [n for n in sub_nodes if n.startswith("vpa:")]
        
        is_abuse_ring = len(component_customers) >= 3 and (len(component_devices) <= 2 or len(component_ips) <= 2)
        
        nodes_data = [{"id": n, "type": self.G.nodes[n].get("type", "unknown"), "label": self.G.nodes[n].get("label", n)} for n in subgraph.nodes()]
        edges_data = [{"source": u, "target": v, "relationship": self.G.edges[u, v].get("relationship", "linked")} for u, v in subgraph.edges()]
        
        return {
            "entity_id": entity_id,
            "target_node": target_node,
            "found": True,
            "nodes": nodes_data,
            "edges": edges_data,
            "ring_metrics": {
                "linked_accounts_count": max(1, len(component_customers)),
                "shared_devices_count": max(1, len(component_devices)),
                "shared_ips_count": max(1, len(component_ips)),
                "shared_vpas_count": len(component_vpas),
                "density": round(nx.density(subgraph), 4),
                "is_abuse_ring_pattern": is_abuse_ring
            }
        }
        
    def get_all_detected_rings(self, min_cluster_accounts=3):
        rings = []
        components = list(nx.connected_components(self.G))
        
        for idx, comp in enumerate(components):
            custs = [n for n in comp if n.startswith("cust:")]
            devs = [n for n in comp if n.startswith("dev:")]
            ips = [n for n in comp if n.startswith("ip:")]
            
            if len(custs) >= min_cluster_accounts:
                rings.append({
                    "ring_id": f"ring_syndicate_{idx:03d}",
                    "account_count": len(custs),
                    "device_count": len(devs),
                    "ip_count": len(ips),
                    "sample_accounts": [c.replace("cust:", "") for c in custs[:5]],
                    "sample_devices": [d.replace("dev:", "") for d in devs[:2]],
                    "threat_level": "CRITICAL" if len(custs) >= 8 else "HIGH"
                })
                
        return rings
