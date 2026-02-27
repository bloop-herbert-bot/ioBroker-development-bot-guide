#!/usr/bin/env python3
"""
ioBroker State Dump via Simple-API
Stable, no race conditions, no SSH filesystem access needed!

Usage: python3 state-dump-api.py <host> <adapter-id> [port]
Example: python3 state-dump-api.py 192.168.1.100 system-health.0 8087
"""

import requests
import sys
import json
from typing import Dict, Any

def fetch_states(host: str, adapter_id: str, port: int = 8087) -> Dict[str, Any]:
    """
    Fetch all states for an adapter via Simple-API REST endpoint.
    
    Args:
        host: ioBroker hostname or IP
        adapter_id: Adapter instance ID (e.g., 'system-health.0')
        port: Simple-API port (default: 8087)
    
    Returns:
        Dict with objects, states, missing states, and stats
    """
    api_url = f"http://{host}:{port}"
    
    # Get objects
    print(f"Fetching objects for {adapter_id}...", file=sys.stderr)
    objects_url = f"{api_url}/getObjects?pattern={adapter_id}.*"
    objects = requests.get(objects_url, timeout=10).json()
    
    # Get states
    print(f"Fetching states for {adapter_id}...", file=sys.stderr)
    states_url = f"{api_url}/getStates?pattern={adapter_id}.*"
    states = requests.get(states_url, timeout=10).json()
    
    # Filter states with values
    states_with_values = {
        k: v for k, v in states.items() 
        if v is not None and v.get('val') is not None
    }
    
    # Find missing
    missing = [k for k in objects.keys() if k not in states_with_values]
    
    return {
        'adapter': adapter_id,
        'host': host,
        'objects': objects,
        'states': states_with_values,
        'missing': missing,
        'stats': {
            'total_objects': len(objects),
            'total_states': len(states_with_values),
            'missing_count': len(missing)
        }
    }

def main():
    if len(sys.argv) < 3:
        print("Usage: state-dump-api.py <host> <adapter-id> [port]")
        print("Example: state-dump-api.py 192.168.1.100 system-health.0 8087")
        sys.exit(1)
    
    host = sys.argv[1]
    adapter_id = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8087
    
    try:
        data = fetch_states(host, adapter_id, port)
        
        # Output JSON
        print(json.dumps(data, indent=2))
        
        # Stats to stderr
        print(f"\n📊 Stats:", file=sys.stderr)
        print(f"  Objects: {data['stats']['total_objects']}", file=sys.stderr)
        print(f"  States:  {data['stats']['total_states']}", file=sys.stderr)
        print(f"  Missing: {data['stats']['missing_count']}", file=sys.stderr)
        
        if data['missing']:
            print(f"\n❌ Missing states:", file=sys.stderr)
            for state_id in data['missing']:
                print(f"  - {state_id}", file=sys.stderr)
    
    except requests.RequestException as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
