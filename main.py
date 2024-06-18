import re
from collections import defaultdict
from csv import DictWriter

def getConfig():
    # Update the path to point to the .txt file
    path = r"C:\Users\Stelaras\Downloads\config1.txt"

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

    try:
        # Read configuration lines from the file
        with open(path, 'r') as file:
            config_lines = file.readlines()
            print("File read successfully.")  # Debug print
            print(f"Number of lines read: {len(config_lines)}")  # Debug print
            print(config_lines)  # Debug print

    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not config_lines:
        print("No lines read from the file.")
        return

    vlans = []
    vlan_config = []

    for line in config_lines:
        stripped_line = line.strip()
        if stripped_line == 'exit':
            vlans.append(' '.join(vlan_config))
            vlan_config = []
        elif stripped_line.startswith('no untagged'):
            continue
        else:
            vlan_config.append(stripped_line)

    if not vlans:
        print("No VLAN configurations found.")
        return

    # Process each VLAN configuration
    for config_line in vlans:
        # Extract VLAN number and tagged/untagged ports
        vlan_number_match = re.search(vlan_pattern, config_line)
        if not vlan_number_match:
            print(f"No VLAN number found in config line: {config_line}")
            continue
        vlan_number = vlan_number_match.group(1)

        tagged_ports_match = re.search(tagged_ports_pattern, config_line)
        untagged_ports_match = re.search(untagged_ports_pattern, config_line)

        tagged_ports = expand_ports(tagged_ports_match.group(1)) if tagged_ports_match else []
        untagged_ports = expand_ports(untagged_ports_match.group(1)) if untagged_ports_match else []

        # Add tagged ports
        for port in tagged_ports:
            if vlan_number not in port_vlan_map[port]['untagged']:  # Ensure the VLAN is not already marked as untagged
                port_vlan_map[port]['tagged'].add(vlan_number)

        # Add untagged ports
        for port in untagged_ports:
            if vlan_number in port_vlan_map[port]['tagged']:  # Remove from tagged if it exists
                port_vlan_map[port]['tagged'].remove(vlan_number)
            port_vlan_map[port]['untagged'].add(vlan_number)

    # Prepare data for CSV
    combined_ports_list = []
    combined_vlans_list = []

    for port in sorted(port_vlan_map.keys(), key=port_sort_key):
        vlans = port_vlan_map[port]
        combined_vlans = []
        if vlans['tagged']:
            combined_vlans.append(f"T: {', '.join(sorted(vlans['tagged'], key=int))}")
        if vlans['untagged']:
            combined_vlans.append(f"U: {', '.join(sorted(vlans['untagged'], key=int))}")
        combined_ports_list.append(port)
        combined_vlans_list.append(' '.join(combined_vlans))

    # Ensure lists are of the same length by padding with empty strings
    max_length = max(len(combined_ports_list), len(combined_vlans_list))

    combined_ports_list.extend([''] * (max_length - len(combined_ports_list)))
    combined_vlans_list.extend([''] * (max_length - len(combined_vlans_list)))

    # Write to CSV
    with open(r"C:\Users\Stelaras\Desktop\Results.csv", "w", newline='') as outputcsv:
        field_names = ['Port', 'VLANs']
        dictWriter = DictWriter(outputcsv, fieldnames=field_names)

        dictWriter.writeheader()

        for i in range(max_length):
            row = {
                'Port': combined_ports_list[i],
                'VLANs': combined_vlans_list[i],
            }
            dictWriter.writerow(row)

if __name__ == '__main__':
    getConfig()
