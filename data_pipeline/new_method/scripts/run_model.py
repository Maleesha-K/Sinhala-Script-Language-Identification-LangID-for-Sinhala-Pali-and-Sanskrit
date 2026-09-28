import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lidlab.data import load_config
from lidlab.experiment import run_experiment

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('model',choices=['nllb','glotlid','conlid'])
    p.add_argument('--config',default='config.json')
    p.add_argument('--phase',default='all',choices=['all','zero_shot','target_only','replay'])
    a=p.parse_args()
    run_experiment(load_config(a.config),a.model,
                   ('zero_shot','target_only','replay') if a.phase=='all' else (a.phase,))
