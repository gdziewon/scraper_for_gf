import logging

def setup_logger(name, session_dir):
    filename = session_dir / f"session.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(filename)
    fh_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(fh_formatter)
    
    # console handler
    ch = logging.StreamHandler()
    ch_formatter = logging.Formatter('%(message)s')
    ch.setFormatter(ch_formatter)
    ch.setLevel(logging.INFO)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger