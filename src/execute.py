import os
import sys
import json
import logging

log = logging.getLogger(__name__)

if __name__ == "__main__":
    # Logging
    logging.basicConfig(format="[ %(asctime)s ] %(name)s | %(levelname)s | %(message)s", datefmt="%m/%d/%Y %I:%M:%S%p", level=logging.INFO)
    log.info(f"Executing: {sys.argv}")
    
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
        config = json.load(fp)
    
    # Run requested mode
    if "search" in sys.argv[1]:
        from twiff import search
        arg_parser = search.get_arg_parser()
        arg_parser.set_defaults(**config)
        args = arg_parser.parse_args([])
        search.main(args)