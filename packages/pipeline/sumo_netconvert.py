import subprocess
import os
import sys

def run_netconvert(osm_file, output_net):
    """
    Run netconvert to convert OSM file to SUMO network.
    """
    # Path to netconvert.exe - adjust if necessary
    netconvert_path = r"C:\Users\tomisu\AppData\Roaming\Python\Python312\Scripts\netconvert.exe"
    
    # Check if netconvert exists
    if not os.path.exists(netconvert_path):
        raise FileNotFoundError(f"netconvert not found at {netconvert_path}")
    
    # Run netconvert
    cmd = [
        netconvert_path,
        "--osm-files", osm_file,
        "-o", output_net
    ]
    
    print(f"Running netconvert: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"netconvert failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError("netconvert failed")
    
    print(f"Successfully created SUMO network: {output_net}")
    return output_net

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sumo_netconvert.py <input.osm> <output.net.xml>")
        sys.exit(1)
    
    osm_file = sys.argv[1]
    output_net = sys.argv[2]
    
    run_netconvert(osm_file, output_net)