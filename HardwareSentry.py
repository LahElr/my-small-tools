import psutil
import argparse
import pynvml
# import GPUtil
# from threading import Thread, Timer
import datetime
import os
import sys
import warnings
import time

def debug_log(*args,**kargs):
    print(*args,**kargs)
    pass

def parse_args_to_boundaries(args):
    boundaries = {}
    args = vars(args)
    for x in ["cpu", "gpu", "mem", "gmem"]:
        if args.get(x, None) is not None:
            boundaries[x] = {}
            for i in range(0, args[x].__len__(), 2):
                if args[x][i] == "part":
                    boundaries[x][args[x][i]] = args[x][i + 1]
                else:
                    boundaries[x][args[x][i]] = float(args[x][i + 1])
    return boundaries


def get_gpu_status():
    gpu_status_list = []
    pynvml.nvmlInit()
    for i in range(pynvml.nvmlDeviceGetCount()):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_status_list.append((mem.free, mem.total, util.gpu/100))
    pynvml.nvmlShutdown()
    return gpu_status_list


class RepeatingTimer:
    '''
    This class executes a function every specified time intervals
    '''
    def __init__(self,interval,function):
        self.interval = interval
        self.function = function
        self.finished = False

    def finish(self):
        self.finished = True

    def run(self):
        while not self.finished:
            try:
                self.function(self)
                time.sleep(self.interval)
            except KeyboardInterrupt:
                debug_log("catch KeyboardInterrupt at run.")
                self.finish()
                break



def get_spec():
    cpu_util = psutil.cpu_percent()/100
    mem_util = psutil.virtual_memory()  # .used  .total
    # psutil.disk_io_counters()  # .read_count  .write_count
    gpu_status = get_gpu_status()
    ret = (cpu_util, mem_util, gpu_status)
    debug_log(ret)
    return ret


def execute_script(platform, script_name, shell_name, output):
    if platform.startswith("linux"):
        if shell_name is None:
            shell_name = "bash"
        try:
            result = os.popen("{} {}".format(shell_name, script_name),
                              mode="r")
        except Exception as e:
            warnings.warn(
                "Following {} has been raised from your script:".format(
                    e.__class__.__name__))
            warnings.warn(e.__str__())
        if output is not None:
            with open(output, "w") as output_f:
                output_f.write(result.read())
        else:
            print(result.read())
    elif platform == "win32" or platform == "cygwin":
        if shell_name is None:
            shell_name = "powershell"
        try:
            result = os.popen("{} {}".format(shell_name, script_name),
                              mode="r")
        except Exception as e:
            warnings.warn(
                "Following {} has been raised from your script:".format(
                    e.__class__.__name__))
            warnings.warn(e.__str__())
        if output is not None:
            with open(output, "w") as output_f:
                output_f.write(result.read())
        else:
            print(result.read())
    elif platform == "darwin":
        # this place is lefted for future
        raise RuntimeError("There's no support for macOS for now.")


request_map = {
    "higher": lambda x, y: x > y,
    "gt": lambda x, y: x > y,
    "lower": lambda x, y: x < y,
    "lt": lambda x, y: x < y,
    "geq": lambda x, y: x >= y,
    "leq": lambda x, y: x <= y,
    "least": lambda x, y: True,
    "most": lambda x, y: True,
    "part": lambda x, y: True
}


def check_gpu_boundaries(bound_util, bound_gmem, gpu_status, gpu_bound_same):
    util_check_list = []
    util_least = 1
    util_most = 99999
    util_request_num_list = []
    gmem_check_list = []
    gmem_least = 1
    gmem_most = 99999
    gmem_request_num_list = []

    for gpu_i, gpu in enumerate(gpu_status):
        gpu_checked = True
        for request, value in bound_util.items():
            gpu_checked = gpu_checked and request_map[request](gpu[2], value)
            if request == "least" and value > util_least:
                util_least = value
            if request == "most" and value < util_most:
                util_most = value
            if request == "part":
                util_request_num_list = map(int,value.split(","))
        if gpu_checked:
            util_check_list.append(gpu_i)

    for gpu_i, gpu in enumerate(gpu_status):
        gpu_checked = True
        for request, value in bound_gmem.items():
            if value <= 1:
                gpu_checked = gpu_checked and request_map[request](
                    gpu[0] / gpu[1],
                    value)  # request value lower than 1: percentage
            elif value > 1:
                gpu_checked = gpu_checked and request_map[request](
                    gpu[0] / 1048576, value)  # request value higher than 1: MB
            if request == "least" and value > gmem_least:
                gmem_least = value
            if request == "most" and value < gmem_most:
                gmem_most = value
            if request == "part":
                gmem_request_num_list = map(int,value.split(","))
        if gpu_checked:
            gmem_check_list.append(gpu_i)

    if not ((util_least <= len(util_check_list) <= util_most) and
            (gmem_least <= len(gmem_check_list) <= gmem_most)):
        return False

    if gpu_bound_same:
        gpu_list = list(set(util_check_list) & set(gmem_check_list))
        gpu_least = max(util_least, gmem_least)
        gpu_max = min(util_most, gmem_most)
        if not (gpu_least <= len(gpu_list) <= gpu_max):
            return False

    for no in util_request_num_list:
        if no not in util_check_list:
            return False

    for no in gmem_request_num_list:
        if no not in gmem_check_list:
            return False

    return True


def check_boundaries(boundaries, specs, gpu_bound_same):
    checked = True
    '''
    specs:(cpu_util,mem_util,[(gmem_free, gmem_total, gpu_util),...])
    boundaries: ["cpu", "gpu", "mem", "gmem"]
    '''
    if "cpu" in boundaries.keys():
        for request, value in boundaries["cpu"].items():
            checked = checked and request_map[request](specs[0], value)
            if checked == False:
                return checked
    if "mem" in boundaries.keys():
        for request, value in boundaries["mem"].items():
            checked = checked and request_map[request](specs[1], value)
            if checked == False:
                return checked
    checked = checked and check_gpu_boundaries(boundaries.get(
        "gpu", {}), boundaries.get("gmem", {}), specs[2], gpu_bound_same)

    return checked


class execute:
    '''
    When called, this class checks whether the hardware
     status can fit the specified boundaries, if can,
     it will execute specified script
    '''
    def __init__(self, args):
        self.boundaries = parse_args_to_boundaries(args)  # parse the requests
        self.script_name = args.script
        self.counter = 0  # for max watch round limit
        self.args = args
        self.platform = sys.platform
        if not ((self.platform.startswith("linux")) or
                (self.platform == "win32" or self.platform == "cygwin")):
            raise RuntimeError(
                "This script only supports Linux and Windows, but you're at {}."
                .format(self.platform))

    def __call__(self, timer):
        debug_log(" --lahelr: script sees.")
        self.counter += 1
        if self.args.max != -1 and self.counter > self.args.max:
            warnings.warn("The limit of max watch times is triggered.")
            timer.finish()
        specs = get_spec()
        if check_boundaries(self.boundaries, specs, args.gpu_bound_same):
            execute_script(self.platform, self.script_name, self.args.sh,
                           args.output)
            timer.finish()


# lahelr: under this line is the area for main()

parser = argparse.ArgumentParser(
    prog="hardware sentry",
    description=
    "This script can watch some specs of cpu or gpu and execute a shell script when they reach set bounds. For operations used to bound specs, higher/gt,lower/lt,geq and leq are supported, for specify gpu number, least and most are supported."
)
parser.add_argument(
    "--cpu",
    type=str,
    default=None,
    dest="cpu",
    nargs="+",
    help=
    "The cpu utility boundary. Use this param like this: \"--cpu higher 0.75\", which means you need cpu utility to be higher than 0.75."
)
parser.add_argument(
    "--gpu",
    type=str,
    default=None,
    dest="gpu",
    nargs="+",
    help=
    "The gpu utility boundary. Use this param like this: \"--gpu higher 0.75 least 3 part 0,1\", which means you need at least 3 GPUs including CPU No.0 and 1 to have a utility over 0.75."
)
parser.add_argument(
    "--mem",
    type=str,
    default=None,
    dest="mem",
    nargs="+",
    help=
    "The mem utility boundary. Use this param like this: \"--mem lower 0.75\", which means you need mem utility to be at most 0.75."
)
parser.add_argument(
    "--gmem",
    type=str,
    default=None,
    dest="gmem",
    nargs="+",
    help=
    "The gpu mem utility boundary. Use this param like this: \"--gmem lower 0.75 least 3\", which means you need at least 3 GPUs to have a mem utility lower than 0.75. You can use a number over 1 to indicate the free GPU-mem, in MB"
)
parser.add_argument("--script",
                    type=str,
                    help="The name of the script you want to exec.",
                    required=True)
parser.add_argument(
    "--step",
    type=float,
    default=1.0,
    help="the time interval of checking hardware specs you want.")
parser.add_argument(
    "--max",
    type=int,
    default=1e4,
    help=
    "The max check rounds you want. Set -1 if you want it to keep checking forever."
)
parser.add_argument(
    "--gpu_bound_same",
    action="store_true",
    help=
    "If you have set the boundary of gpu mem and utility, set this param means you want the GPUs to fit boundaries both side simultaneously when the scripts are executed."
)
parser.add_argument(
    "--sh",
    type=str,
    default=None,
    help=
    "The shell you want to be used to execute your script. In linux, default is bash; in windows, default is powershell."
)
parser.add_argument(
    "--output",
    type=str,
    default=None,
    help="the log file you want to put the output of your script.")
args = parser.parse_args()

if args.step < 0.1:
    raise RuntimeError(
        "The time step is too short, please set it to over 0.1 sec.")

t = RepeatingTimer(1.0, execute(args))  # set the repeating timer
t.run()  # start watching
