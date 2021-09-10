import psutil
import argparse
# import GPUtil
# from threading import Thread, Timer
import datetime
import os
import sys
import warnings
import time
import shutil

# In case you don't have any nvidia GPUs
try:
    import pynvml
    pynvml.nvmlInit()
    pynvml.nvmlShutdown()
except OSError:

    class pynvml:
        @classmethod
        def nvmlInit(x):
            pass

        @classmethod
        def nvmlShutdown(x):
            pass

        @classmethod
        def nvmlDeviceGetCount(x):
            return 0


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


def get_temps():
    try:
        temp_list = psutil.sensors_temperatures(fahrenheit=False)
        ret = {}
        for k in temp_list.keys():
            report_list = []
            for d in temp_list[k]:
                report_list.append((d.label, d.current, d.high, d.critical))
            ret[k] = report_list
        return ret
    except:
        return None


class RepeatingTimer:
    '''
    This class executes a function every specified time intervals
    '''

    def __init__(self, interval, function):
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


def get_spec(specs_need=[True for _ in range(7)]):
    # cpu_util = [psutil.cpu_percent(x) for x in range(psutil.cpu_count())] # why getting logic cpu util can cost that much time?
    cpu_util = psutil.cpu_percent() if specs_need[0] else None

    # .used  .total  .free  .percent
    mem_util = [psutil.virtual_memory(),
                psutil.swap_memory()] if specs_need[1] else None

    # .total  .used  .free  .percent
    disk_usage = psutil.disk_usage("/") if specs_need[2] else None

    # .read_count  .write_count
    disk_util = psutil.disk_io_counters() if specs_need[3] else None

    net_util = psutil.net_io_counters() if specs_need[4] else None

    gpu_status = get_gpu_status() if specs_need[5] else None

    temps = get_temps() if specs_need[6] else None

    ret = [cpu_util, mem_util, disk_usage,
           disk_util, net_util, gpu_status, temps]
    return ret


def warp_line(line: str, col: int):
    ret = []
    while True:
        if len(line) <= col:
            ret.append(line)
            break
        else:
            space_positions = [i for i in range(len(line)) if line[i] == " "]
            split_index = 0
            for space_position in space_positions:
                if space_position > split_index:
                    if space_position <= col:
                        split_index = space_position
                    else:
                        break
            if split_index == 0:
                split_index = col
            ret.append(line[:split_index])
            line = line[split_index:]
    return ret


def warp_lines(content: str):
    lines = content.splitlines()
    col, row = shutil.get_terminal_size()
    ret = []
    for i, line in enumerate(lines):
        ret.extend(warp_line(line, col))
    return ret


def flushing_content(i: int, content: str):
    lines = warp_lines(content)
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
    '''Each item in specs may be None
    specs:
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
        ],
        {
            label:[
                (
                    label, current_temp, high_temp, critical_temp
                ),
                ...
            ],
            ...
        }
    ]
    '''
    content = "-" * 7
    content += "\n"
    content += "Time : {}\n".format(datetime.datetime.now())

    if specs[0] is not None:
        content += "CPU util: {}%.\n".format(specs[0])

    if specs[1] is not None:
        content += "Virtual Memory: {}/{} bytes used, {}/{} bytes free, util {}%.\n".format(
            specs[1][0].used, specs[1][0].total, specs[1][0].free,
            specs[1][0].total, specs[1][0].percent)
        content += "Swap Memory: {}/{} bytes used, {}/{} bytes free, util {}%.\n".format(
            specs[1][1].used, specs[1][1].total, specs[1][1].free,
            specs[1][1].total, specs[1][1].percent)

    if specs[2] is not None:
        content += "Disk: {} used, {} free, {} total, util {}%.\n".format(
            specs[2].used, specs[2].free, specs[2].total, specs[2].percent)

    if specs[3] is not None:
        content += "Disk IO: read {}, write {}, r/w ratio {:.2f}.\n".format(
            specs[3].read_count, specs[3].write_count,
            (specs[3].read_count / specs[3].write_count))
        content += "Dist IO time: read {}, write {}, r/w ratio {:.2f}.\n".format(
            specs[3].read_time, specs[3].write_time,
            (specs[3].read_time / specs[3].write_time))

    if specs[4] is not None:
        content += "Net IO: {} packets sent, {} packets recv, errin {}, errout {}.\n".format(
            specs[4].packets_sent, specs[4].packets_recv, specs[4].errin,
            specs[4].errout)

    if specs[5] is not None and len(specs[5]) > 0:
        content += "GPU status:\n"
        for gpu_no, gpu in enumerate(specs[5][:-1]):
            content += "├-GPU No.{} : {}:\n".format(gpu_no, gpu[0].decode())
            content += "| ├-GPU Memory: {} bytes used, {} bytes free, {} bytes total, util {:.2f}%.\n".format(
                gpu[1].used, gpu[1].free, gpu[1].total,
                (gpu[1].used / gpu[1].total * 100))
            content += "| └-GPU Utilization: {}%.\n".format(gpu[2].gpu)
        gpu_no = len(specs[5]) - 1
        gpu = specs[5][-1]
        content += "└-GPU No.{} : {}:\n".format(gpu_no, gpu[0].decode())
        content += "  ├-GPU Memory: {} bytes used, {} bytes free, {} bytes total, util {:.2f}%.\n".format(
            gpu[1].used, gpu[1].free, gpu[1].total,
            (gpu[1].used / gpu[1].total * 100))
        content += "  └-GPU Utilization: {}%.\n".format(gpu[2].gpu)

    if specs[6] is not None:
        temperature_unit = "℃"  # ℉
        content += "Temperature:\n"
        keys = list(specs[6].keys())
        for k in keys[:-1]:
            content += "├-{}:\n".format(k)
            if len(specs[6][k]) > 0:
                for device in specs[6][k][:-1]:
                    content += "├ ├-{}:current {}{}, high {}{} /critical {}{}.\n".format(
                        device[0], device[1], temperature_unit, device[2], temperature_unit, device[3], temperature_unit)
                content += "├ └-{}:current {}{}, high {}{} /critical {}{}.\n".format(
                    specs[6][k][-1][0], specs[6][k][-1][1], temperature_unit, specs[6][k][-1][2], temperature_unit, specs[6][k][-1][3], temperature_unit)
        k = keys[-1]
        content += "└-{}:\n".format(k)
        if len(specs[6][k]) > 0:
            for device in specs[6][k][:-1]:
                content += "  ├-{}:current {}{}, high {}{} /critical {}{}.\n".format(
                    device[0], device[1], temperature_unit, device[2], temperature_unit, device[3], temperature_unit)
            content += "  └-{}:current {}{}, high {}{} /critical {}{}.\n".format(
                specs[6][k][-1][0], specs[6][k][-1][1], temperature_unit, specs[6][k][-1][2], temperature_unit, specs[6][k][-1][3], temperature_unit)

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
            specs = get_spec(self.args.specs_need)
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

specs_len = 7

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
parser.add_argument(
    "--need",
    type=str,
    default=str(2**specs_len - 1),
    help="Integer. Each bit tells whether you want to see the spec: CPU_util, mem_util, disk_usage, disk_util, net_util, GPU_status, temps. You can also use 0x/0b/0o prefix to use hexadecimal/binary/octonary."
)
args = parser.parse_args()

if args.step < 0.1:
    raise RuntimeError(
        "The time step is too short, please set it to over 0.1 sec.")

if args.need.startswith("0b"):
    args_need = int(args.need,base=2)
elif args.need.startswith("0o"):
    args_need = int(args.need,base=8)
elif args.need.startswith("0x"):
    args_need = int(args.need,base=16)
else:
    args_need = int(args.need)
specs_need = [False for _ in range(specs_len)]
for i,_ in enumerate(specs_need):
    specs_need[specs_len - 1 - i] = (args_need & 1<<i) != 0

setattr(args, "specs_need", specs_need)

t = RepeatingTimer(1.0, execute(args))  # set the repeating timer
t.run()  # start watching
