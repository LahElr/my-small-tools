# my-small-tools

---

<center>
  <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">
    <center><img alt="知识共享许可协议" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></center>
  </a>
</center>

本作品采用<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">知识共享署名-非商业性使用-相同方式共享 4.0 国际许可协议</a>进行许可。

This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

---

## DirMerger

This script can merge 2 directions in the way you want.

Need python 3, all packages used are python standard libraries.

For detail, see the help documention built inside the script by `argparse`

## SBU Crawler

This script can crawl images of dataset SBU dataset mentioned in [Im2Text: Describing Images Using 1 Million Captioned Photographs](http://www.cs.virginia.edu/~vicente/sbucaptions/) with proxy.

## Hardware Sentry

This script can watch some specs of CPU or GPU and execute a shell script when they reach set bounds. For operations used to bound specs, higher/gt,lower/lt,geq and leq are supported, for specify gpu number, least and most are supported.

For now, it only support Windows or Linux machines. Only Nvidia GPUs are supported. Multiple GPU is supported, but multiple CPU is not. MacOS devices are not supported as I don't have such one.

Need cuda, pynvml and psutil.

While using this script, please note to make sure to redirect output of commands in the shell script. For Linux/Windows, use `command &> log` to get all outputs.
