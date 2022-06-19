import os
import sys
import uuid
import json
import logging
from importlib import import_module

log = logging.getLogger(__name__)


def main():
    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="Twitter4Future: [ %(asctime)s ] %(name)s | %(levelname)s | %(message)s", 
        datefmt="%m/%d/%Y %I:%M:%S%p", 
        handlers = [
            logging.FileHandler(f"/home/deploy/gamechanger/twiff/logs/out.log", mode='a'),
            logging.StreamHandler()
        ]
    )
    log.info(f"Executing {sys.argv[1]}...")
    
    # Ensure correct number of args
    if len(sys.argv) < 3:
        log.warning(f"Require use instruction and config file as an argument.")
        sys.exit(1)
        
    # Ensure src path is in sys path
    base_path = os.path.dirname(os.path.realpath(__file__))
    if not base_path in sys.path:
        sys.path.append(base_path)
        
    # Load configuration for run
    with open(sys.argv[2], 'r') as fp:
        args = json.load(fp)
        
    # Execute requested mode
    module = import_module(f"twiff.{sys.argv[1]}")
    module.main(args)

if __name__ == "__main__":
    main()
