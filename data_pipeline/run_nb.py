import sys
import json
import os
import subprocess

def run_notebook(nb_path):
    print(f"Extracting code from {nb_path}...")
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    code_cells = [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
    script_path = nb_path.replace('.ipynb', '.py')
    
    with open(script_path, 'w', encoding='utf-8') as f:
        for cell in code_cells:
            for line in cell:
                # Remove any pip installs or colab specific lines
                if not line.startswith('!') and not line.startswith('%'):
                    f.write(line)
            f.write('\n\n')
            
    print(f"Running {script_path}...")
    cwd = os.path.dirname(os.path.abspath(__file__)) # this is data_pipeline
    
    env = os.environ.copy()
    env["HF_TOKEN"] = os.environ.get("HF_TOKEN", "") # removed hardcoded token for security
    
    result = subprocess.run([sys.executable, os.path.abspath(script_path)], cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_path}:\n{result.stderr}")
    else:
        print(f"Successfully ran {script_path}:\n{result.stdout}")

if __name__ == '__main__':
    run_notebook(sys.argv[1])
