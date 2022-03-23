from importlib import import_module

def load_module(config, module, **kwargs):
    if f"{module}" in config: 
        module_config = config[f"{module}"]
        func_module = import_module(module_config["module"])
        func_call = getattr(func_module, module_config["call"])
        func_kwargs = {**kwargs, **module_config["config"]} if "config" in module_config else {**kwargs}
        return func_call(**func_kwargs)
    else:
        return None