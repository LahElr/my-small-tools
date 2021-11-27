import argparse
import os
import shutil

# python .\DirMerger.py -t=test\dest -s=test\src -a=0
# python .\DirMerger.py -t=test\dest -s=test\src -a=15


def file_name_with_sub_struct(root_path: str, parent: str,
                              filename: str) -> str:
    return os.path.join(parent.split(root_path)[1],
                        filename).replace("\\", "_")[1:]


def rec_delete_files(path: str) -> None:
    cur_path = os.path.dirname(path) if os.path.isfile(path) else path
    cur_path = os.path.abspath(cur_path)
    # print(path)
    # print(cur_path)
    for parent, dirnames, filenames in os.walk(cur_path):
        # for dirname in dirnames
        for filename in filenames:
            print("deleting file: {}".format(os.path.join(parent, filename)))
            os.remove(os.path.join(parent, filename))


def delete_dirs(path: str) -> None:
    cur_path = os.path.dirname(path) if os.path.isfile(path) else path
    cur_path = os.path.abspath(cur_path)
    # print(path)
    # print(cur_path)
    for node in os.listdir(cur_path):
        node_path = os.path.join(cur_path, node)
        if os.path.isdir(node_path):
            print("deleting {}".format(node_path))
            shutil.rmtree(node_path)


def rec_move_files_to_root(root_path: str) -> None:
    cur_path = os.path.dirname(root_path) if os.path.isfile(
        root_path) else root_path
    cur_path = os.path.abspath(cur_path)
    # print(path)
    # print(cur_path)
    for parent, dirnames, filenames in os.walk(cur_path):
        # for dirname in dirnames
        for filename in filenames:
            print("moving file: {}".format(os.path.join(parent, filename)))
            new_name = file_name_with_sub_struct(root_path, parent, filename)
            #print(new_name)
            os.rename(os.path.join(parent, filename),
                      os.path.join(parent, new_name))
            shutil.move(os.path.join(parent, new_name), root_path)


def delete_under_dir(root_path: str) -> None:
    cur_path = os.path.dirname(root_path) if os.path.isfile(
        root_path) else root_path
    cur_path = os.path.abspath(cur_path)
    # print(path)
    # print(cur_path)
    for node in os.listdir(cur_path):
        print("deleting {}".format(os.path.join(cur_path, node)))
        shutil.rmtree(os.path.join(cur_path, node))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s",
                        "--src",
                        default=".",
                        help="the source direction",
                        type=str)
    parser.add_argument("-t",
                        "--destination",
                        help="the destination direction",
                        type=str,
                        required=True)
    parser.add_argument(
        "-a",
        "--action",
        help=
        "how to merge, consist of 4 bits, specifies whether you want to :keep the src files, keep the src dir-struct, keep the dest files, keep the dest dir-struct.",
        type=int,
        default=15,
        choices=range(16))
    parser.add_argument(
        "-k",
        "--keep",
        help=
        "bool, keep the src file not moved or copied if a file with same name exists in destination",
        default=True,
        action="store_true")
    parser.add_argument("-d",
                        "--detailed",
                        help="bool, whether you want to see detailed info",
                        default=True,
                        action="store_true")
    args = parser.parse_args()

    # print("\n".join(
    #     ["{}:{}".format(i[0], i[1]) for i in args.__dict__.items()]))
    # 1.留下源文件吗？2.留下源目录结构吗？3.留下目标文件吗？4.留下目标目录结构吗？
    keep_src_file = args.action & 8 != 0
    keep_src_dir = args.action & 4 != 0
    keep_dest_file = args.action & 2 != 0
    keep_dest_dir = args.action & 1 != 0
    print("src:{}".format(args.src))
    print("dest:{}".format(args.destination))
    print("action:{},{},{},{}".format(keep_src_file, keep_src_dir,
                                      keep_dest_file, keep_dest_dir))
    print("keep:{}, detailed:{}.".format(args.keep, args.detailed))

    print("are you sure to continue? your", end="")
    if args.action == 15:
        print(" nothing", end="")
    else:
        for i in {
                8: "source files",
                4: "source direction structure",
                2: "original files in destination path",
                1: "original direction structure in destination path"
        }.items():
            if args.action & i[0] == 0:
                print(" {},".format(i[1]), end="")
    print(" will be deleted.[Y/N]")
    if input().strip().lower() != "y":
        print("stop.")
        exit(0)

    # preprocess the target dir
    if not keep_dest_file and keep_dest_dir:
        rec_delete_files(args.destination)
    if not keep_dest_dir and keep_dest_file:
        rec_move_files_to_root(args.destination)
        delete_dirs(args.destination)
    if not keep_dest_dir and not keep_dest_file:
        delete_under_dir(args.destination)

    # start mov/cp
    src_full_path = os.path.dirname(args.src) if os.path.isfile(
        args.src) else args.src
    src_full_path = os.path.abspath(src_full_path)

    dest_full_path = os.path.dirname(args.destination) if os.path.isfile(
        args.destination) else args.destination
    dest_full_path = os.path.abspath(dest_full_path)

    for parent, dirnames, filenames in os.walk(src_full_path):
        # print("looping in {},{},{}".format(parent, dirnames, filenames))
        for dirname in dirnames:
            # print("looping in {} under {}.".format(dirname, parent))
            dest_sub_dir = os.path.join(dest_full_path,
                                        parent.split(src_full_path)[1][1:])
            if not os.path.exists(dest_sub_dir):
                os.makedirs(dest_sub_dir)

        for filename in filenames:
            # print("looping in {} under {}.".format(filename, parent))
            dest_sub_dir = os.path.join(dest_full_path,
                                        parent.split(src_full_path)[1][1:])
            lsd = []
            try:
                lsd = os.listdir(dest_sub_dir)
            except FileNotFoundError or NotADirectoryError:
                pass
            nn = ""
            if filename in lsd:
                if args.keep:
                    print(
                        "{} is omitted duo to a same-name-file in destination."
                        .format(os.path.join(parent, filename)))
                    continue
                else:
                    lss = os.listdir(parent)
                    for i in range(65536):
                        nn = "src{}_{}".format(i, filename)
                        if nn not in lss and nn not in lsd:
                            os.rename(os.path.join(parent, filename),
                                      os.path.join(parent, nn))
                            break
                        if i >= 65535:
                            raise RuntimeError(
                                "too many iters of a same-name-file.")
            else:
                nn = filename

            print(dest_sub_dir, dest_full_path)
            if not os.path.exists(dest_sub_dir):
                os.makedirs(dest_sub_dir)

            if keep_src_file:
                if args.detailed:
                    print("coping file {} to {}".format(
                        os.path.join(parent, nn),
                        os.path.join(dest_sub_dir, nn)))
                shutil.copy(os.path.join(parent, nn), dest_sub_dir)
                # shutil.copy(os.path.join(parent,nn),os.path.join(dest_sub_dir,nn))
            else:
                if args.detailed:
                    print("moving file {} to {}".format(
                        os.path.join(parent, nn), dest_sub_dir))
                shutil.move(os.path.join(parent, nn), dest_sub_dir)

    if not keep_src_dir:
        rec_move_files_to_root(args.src)
        delete_dirs(args.src)

    print("finished.")
