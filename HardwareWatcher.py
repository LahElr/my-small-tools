import psutil
import argparse
import pynvml
# import GPUtil
from threading import Thread, Timer
import datetime
import os
import sys
import warnings
import time


def debug_log(*args, **kargs):
    # print(*args, **kargs)
    pass


def get_gpu_status():
    gpu_status_list = []
    pynvml.nvmlInit()
    for i in range(pynvml.nvmlDeviceGetCount()):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_status_list.append((name, mem, util))
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
    # cpu_util = [psutil.cpu_percent(x) for x in range(psutil.cpu_count())] # why getting logic cpu util can cost that much time?
    cpu_util = psutil.cpu_percent()
    mem_util = [psutil.virtual_memory(),
                psutil.swap_memory()]  # .used  .total  .free  .percent
    disk_usage = psutil.disk_usage("/")  # .total  .used  .free  .percent
    disk_util = psutil.disk_io_counters()  # .read_count  .write_count
    net_util = psutil.net_io_counters()
    gpu_status = get_gpu_status()
    ret = [cpu_util, mem_util, disk_usage, disk_util, net_util, gpu_status]
    return ret


def flushing_content(i: int, content: str):
    lines = content.splitlines()
    line_count = len(lines)
    if i > 0:
        for _ in range(line_count - 1):
            sys.stdout.write(u"\u001b[1A")
    for line_no, line in enumerate(lines):
        sys.stdout.write(u"\u001b[1000D\u001b[2K" + line)
        if not line_no == line_count - 1:
            sys.stdout.write(u"\n")
    sys.stdout.flush()


def output_specs(report_num, specs):
    '''specs:
    [
        cpu_util,
        [
            vmem_util(.used  .total  .free  .percent),
            swap_util(.used  .total  .free  .percent)
        ],
        disk_usage(.total  .used  .free  .percent),
        disk_util(# .read_count  .write_count),
        net_util,
        [
            (
                gpu_name,
                gpu_mem(.free  .total  .used),
                gpu_util(.gpu)
            ),
            ...
        ]
    ]
    '''
    content = "-" * 7
    content += "\n"
    content += "Time : {}\n".format(datetime.datetime.now())

    content += "CPU util: {}%.\n".format(specs[0])
    content += "Virtual Memory: {}/{} bytes used, {}/{} bytes free, util {}%.\n".format(
        specs[1][0].used, specs[1][0].total, specs[1][0].free,
        specs[1][0].total, specs[1][0].percent)
    content += "Swap Memory: {}/{} bytes used, {}/{} bytes free, util {}%.\n".format(
        specs[1][1].used, specs[1][1].total, specs[1][1].free,
        specs[1][1].total, specs[1][1].percent)

    content += "Disk: {} used, {} free, {} total, util {}%.\n".format(
        specs[2].used, specs[2].free, specs[2].total, specs[2].percent)
    content += "Disk IO: read {}, write {}, r/w ratio {:.2f}.\n".format(
        specs[3].read_count, specs[3].write_count,
        (specs[3].read_count / specs[3].write_count))
    content += "Dist IO time: read {}, write {}, r/w ratio {:.2f}.\n".format(
        specs[3].read_time, specs[3].write_time, (specs[3].read_time/specs[3].write_time))
    content += "Net IO: {} packets sent, {} packets recv, errin {}, errout {}.\n".format(
        specs[4].packets_sent, specs[4].packets_recv, specs[4].errin,
        specs[4].errout)

    content += "GPU status:\n"
    for gpu_no, gpu in enumerate(specs[5][:-1]):
        content += "├-GPU No.{} : {}:\n".format(gpu_no, gpu[0].decode())
        content += "| ├-GPU Memory: {} bytes used, {} bytes free, {} bytes total, util {:.2f}%.\n".format(
            gpu[1].used, gpu[1].free, gpu[1].total, (gpu[1].used / gpu[1].total * 100))
        content += "| └-GPU Utilization: {}%.\n".format(gpu[2].gpu)
    gpu_no = len(specs[5]) - 1
    gpu = specs[5][-1]
    content += "└-GPU No.{} : {}:\n".format(gpu_no, gpu[0].decode())
    content += "  ├-GPU Memory: {} bytes used, {} bytes free, {} bytes total, util {:.2f}%.\n".format(
        gpu[1].used, gpu[1].free, gpu[1].total, (gpu[1].used / gpu[1].total * 100))
    content += "  └-GPU Utilization: {}%.\n".format(gpu[2].gpu)

    content += "-" * 7
    content += "\n\n"
    flushing_content(report_num, content)


class execute:
    def __init__(self, args):
        self.counter = 0  # for max watch round limit
        self.args = args

    def __call__(self, timer):
        try:
            debug_log(" --lahelr: script sees.")
            specs = get_spec()
            output_specs(self.counter, specs)
            self.counter += 1
            if self.args.max != -1 and self.counter >= self.args.max:
                warnings.warn("The limit of max watch times is triggered.")
                timer.finish()
        except KeyboardInterrupt:
            debug_log("catch KeyboardInterrupt at execute.")
            timer.finish()
            raise KeyboardInterrupt()


# lahelr: under this line is the area for main()

parser = argparse.ArgumentParser(
    prog="hardware watcher",
    description="This script can watch some specs of cpu or gpu and report them.")
parser.add_argument(
    "--step",
    type=float,
    default=1.0,
    help="the time interval of checking hardware specs you want.")
parser.add_argument(
    "--max",
    type=int,
    default=1e4,
    help="The max check rounds you want. Set -1 if you want it to keep checking forever."
)
args = parser.parse_args()

if args.step < 0.1:
    raise RuntimeError(
        "The time step is too short, please set it to over 0.1 sec.")

t = RepeatingTimer(1.0, execute(args))  # set the repeating timer
t.run()  # start watching
