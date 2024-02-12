# my-small-tools

---

## DirMerger

This script can merge 2 directions in the way you want.

For detail, see the help messages built inside the script.

## Hardware Sentry

This script can watch some specs of CPU or GPU and execute a shell script when they reach set bounds. For operations used to bound specs, higher/gt,lower/lt,geq and leq are supported, for specify gpu number, least and most are supported.

For now, it only support Windows or Linux machines. Only Nvidia GPUs are supported. Multiple GPU is supported, but multiple CPU is not. MacOS devices are not supported.

Requires cuda, pynvml and psutil.

While using this script, please note to make sure to redirect output of commands in the shell script. For Linux/Windows, use `command &> log` to get all outputs.

## Hardware Watcher

This script can report some hardware performance data routinely, kinda like a very simple mix of htop and nvidia-smi.

Requires psutil. Requires cuda and pynvml to see GPU informations. For GPU information, only Nvidia GPUs are supported.

This script reuses some of the code from [Hardware Sentry](https://github.com/LahElr/my-small-tools#hardware-sentry) [here](https://github.com/LahElr/my-small-tools/blob/main/HardwareSentry.py).

Tested on Windows and Linux machines. It should also work on other OSs, but no test is done. Functions about temperature are only avaliable on Linux.

## SBU Crawler

This script can crawl images of dataset SBU dataset mentioned in [Im2Text: Describing Images Using 1 Million Captioned Photographs](http://www.cs.virginia.edu/~vicente/sbucaptions/) with proxy.

## CatPuzzleGameSolver

This script solves the game Cat Organized Neatly, a result of me stuck at one stage for over 30 minutes.
