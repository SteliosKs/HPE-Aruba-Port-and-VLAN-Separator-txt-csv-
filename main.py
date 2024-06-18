import re
from collections import defaultdict
from csv import DictWriter

def getConfig():
    path = " "

    vlan_pattern = r'vlan (\d+)'
    tagged_ports_pattern = r'tagged ([A-Z0-9,-]+)'
    untagged_ports_pattern = r'untagged ([A-Z0-9,-]+)'

    # Function to expand port ranges
    def expand_ports(port_str):
        expanded_ports = []
        port_groups = port_str.split(',')
        for group in port_groups:
            if '-' in group:
                prefix = re.match(r'([A-Z]+)', group).group(1)  # Extract the letter prefix
                start, end = re.findall(r'(\d+)', group)  # Extract the numeric range
                expanded_ports.extend([f"{prefix}{i}" for i in range(int(start), int(end) + 1)])
            else:
                expanded_ports.append(group)
        return expanded_ports

    # Initialize the port map
    port_vlan_map = defaultdict(lambda: {'tagged': set(), 'untagged': set()})  # Use sets to avoid duplicates

    def port_sort_key(port):
        match = re.match(r'([A-Z]+)(\d+)', port)
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            return (prefix, number)
        return port

    # Read configuration lines from the file
    with open(r"MockDoc.txt", "r") as file:
        config_lines = file.readlines()

    # Process each configuration line
    for config_line in config_lines:
        # Extract VLAN number and tagged/untagged ports
        vlan_number = re.search(vlan_pattern, config_line).group(1)
        tagged_ports_match = re.search(tagged_ports_pattern, config_line)
        untagged_ports_match = re.search(untagged_ports_pattern, config_line)

        tagged_ports = expand_ports(tagged_ports_match.group(1)) if tagged_ports_match else []
        untagged_ports = expand_ports(untagged_ports_match.group(1)) if untagged_ports_match else []

        # Add untagged ports first to ensure they override tagged entries
        for port in untagged_ports:
            port_vlan_map[port]['untagged'].add(vlan_number)
            if vlan_number in port_vlan_map[port]['tagged']:
                port_vlan_map[port]['tagged'].remove(vlan_number)

        # Add tagged ports
        for port in tagged_ports:
            if vlan_number not in port_vlan_map[port]['untagged']:
                port_vlan_map[port]['tagged'].add(vlan_number)

    # Create the final port_vlan_map with aggregated T: and U: entries
    final_port_vlan_map = {}
    for port, vlans in port_vlan_map.items():
        final_vlans = []
        if vlans['tagged']:
            final_vlans.append(f"T:{','.join(sorted(vlans['tagged'], key=int))}")
        if vlans['untagged']:
            final_vlans.append(f"U:{','.join(sorted(vlans['untagged'], key=int))}")
        final_port_vlan_map[port] = final_vlans

    sorted_ports = sorted(final_port_vlan_map.keys(), key=port_sort_key)

    max_port_length = max(len(port) for port in sorted_ports)
    max_vlan_length = max(len(', '.join(vlans)) for vlans in final_port_vlan_map.values())

    with open("Results.csv", "w", newline='') as outputcsv:
        field_names = ['Port', 'VLANs']
        dictWriter = DictWriter(outputcsv, fieldnames=field_names)

        dictWriter.writeheader()

        for port in sorted_ports:
            vlans = ', '.join(final_port_vlan_map[port])
            pairDict = {
                'Port': port.ljust(max_port_length),
                'VLANs': vlans.ljust(max_vlan_length)
            }
            dictWriter.writerow(pairDict)

if __name__ == '__main__':
    getConfig()
