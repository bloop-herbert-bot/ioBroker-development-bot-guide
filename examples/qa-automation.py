#!/usr/bin/env python3
"""
Automated QA Testing for ioBroker Adapters
Tests state initialization and finds missing states.

Usage: python3 qa-automation.py <host> <adapter-id> <config-file>
Example: python3 qa-automation.py 192.168.1.100 system-health.0 qa-config.json
"""

import requests
import sys
import json
from collections import defaultdict
from typing import Dict, List, Any

def load_config(config_file: str) -> Dict[str, Any]:
    """Load QA config file."""
    with open(config_file, 'r') as f:
        return json.load(f)

def fetch_states(host: str, adapter_id: str, port: int = 8087) -> Dict[str, Any]:
    """Fetch states via Simple-API."""
    api_url = f"http://{host}:{port}"
    objects = requests.get(f"{api_url}/getObjects?pattern={adapter_id}.*", timeout=10).json()
    states = requests.get(f"{api_url}/getStates?pattern={adapter_id}.*", timeout=10).json()
    return {'objects': objects, 'states': states}

def analyze_bugs(data: Dict[str, Any], features: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze states and find bugs."""
    bugs = []
    
    for state_id, meta in features.items():
        full_id = f"{data['adapter_id']}.{state_id}"
        has_object = full_id in data['objects']
        has_state = full_id in data['states']
        state_val = data['states'].get(full_id, {}).get('val')
        
        # Bug Pattern 1: Missing State
        if has_object and not has_state:
            bugs.append({
                'type': 'missing_state',
                'state_id': state_id,
                'feature': meta['name'],
                'critical': meta['critical'],
                'pattern': 'Object defined, state never set'
            })
        
        # Bug Pattern 2: Null Value
        elif has_state and state_val is None:
            bugs.append({
                'type': 'null_value',
                'state_id': state_id,
                'feature': meta['name'],
                'critical': meta['critical'],
                'pattern': 'State exists but val=null'
            })
    
    return bugs

def group_bugs_by_feature(bugs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group bugs by feature."""
    bug_groups = defaultdict(list)
    for bug in bugs:
        bug_groups[bug['feature']].append(bug)
    return dict(bug_groups)

def generate_report(adapter_id: str, bug_groups: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate human-readable QA report."""
    report = f"\n🧪 **QA Report: {adapter_id}**\n\n"
    
    if not bug_groups:
        report += "✅ All states initialized correctly!\n"
        return report
    
    total_bugs = sum(len(bugs) for bugs in bug_groups.values())
    report += f"🐛 **Bugs found:** {total_bugs} states in {len(bug_groups)} features\n\n"
    
    for feature_name, bugs in bug_groups.items():
        critical_count = sum(1 for b in bugs if b['critical'])
        icon = '🔴' if critical_count > 0 else '🟡'
        
        report += f"{icon} **{feature_name}** ({len(bugs)} states)\n"
        report += f"   Critical: {critical_count}, Info: {len(bugs) - critical_count}\n"
        
        for bug in bugs:
            state_icon = '🔴' if bug['critical'] else '🟡'
            report += f"   {state_icon} `{bug['state_id']}` - {bug['type'].replace('_', ' ').title()}\n"
        
        report += "\n"
    
    return report

def main():
    if len(sys.argv) < 4:
        print("Usage: qa-automation.py <host> <adapter-id> <config-file>")
        print("Example: qa-automation.py 192.168.1.100 system-health.0 qa-config.json")
        sys.exit(1)
    
    host = sys.argv[1]
    adapter_id = sys.argv[2]
    config_file = sys.argv[3]
    
    # Load config
    config = load_config(config_file)
    features = config.get('features', {})
    
    # Fetch states
    print(f"📊 Fetching states from {host}...", file=sys.stderr)
    data = fetch_states(host, adapter_id)
    data['adapter_id'] = adapter_id
    
    # Analyze bugs
    print(f"🔍 Analyzing states...", file=sys.stderr)
    bugs = analyze_bugs(data, features)
    
    # Group by feature
    bug_groups = group_bugs_by_feature(bugs)
    
    # Generate report
    report = generate_report(adapter_id, bug_groups)
    print(report)
    
    # Exit code: 0 if no bugs, 1 if bugs found
    sys.exit(1 if bug_groups else 0)

if __name__ == '__main__':
    main()
