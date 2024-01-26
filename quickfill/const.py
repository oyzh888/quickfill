import os
import pathlib
import time
import uuid

TRUE_CUR_PATH = os.path.dirname(__file__)
TRUE_CUR_PATH = TRUE_CUR_PATH if TRUE_CUR_PATH != "" else "."

pl_TRUE_CUR_PATH = pathlib.Path(TRUE_CUR_PATH)
BASE_PATH = pl_TRUE_CUR_PATH.parent.parent
DATA_PATH = BASE_PATH / 'data'
CACHE_PATH = DATA_PATH / 'cache'
CACHE_PATH.mkdir(parents=True, exist_ok=True)

# Check the auto root path is correct
try:
    assert BASE_PATH.name == "quickfill"
except Exception as e:
    print("Base dir should be something like ....../quickfill/: ", BASE_PATH)
    print("Important! Ensure TRUE_CUR_PATH is your working directory:", TRUE_CUR_PATH)
    print("Exception:", e)


def generate_random_id(length=36):
    return str(uuid.uuid4())[:length]


def time_it(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        print(f"### Function {func.__name__!r} executed in {(t2 - t1):.4f}s ###")
        return result

    return wrap_func

