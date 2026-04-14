#!/usr/bin/python3

import os
import sys
import shutil


def main(source, dest, sourceuid, destuid):
    sourceuid = int(sourceuid)
    destuid = int(destuid)
    ap = os.path.abspath(source)
    for root, dirs, files in os.walk(ap, topdown=False):
        for p in dirs + files:
            oldpath = os.path.join(root, p)
            current = os.lstat(oldpath)
            new_uid = (current.st_uid - sourceuid) + destuid
            new_gid = (current.st_gid - sourceuid) + destuid
            newpath = os.path.join(dest, os.path.relpath(oldpath, ap))
            if not os.path.islink(oldpath) and os.path.isdir(oldpath):
                if not os.path.isdir(newpath):
                    if os.path.lexists(newpath):
                        os.unlink(newpath)
                    os.makedirs(newpath)
                    shutil.copystat(oldpath, newpath, follow_symlinks=False)
            else:
                if not os.path.islink(newpath) and os.path.isdir(newpath):
                    shutil.rmtree(newpath)
                #elif os.path.exists(newpath):
                #    os.unlink()
                parent = os.path.dirname(newpath)
                if not os.path.exists(parent):
                    os.makedirs(parent)
                os.rename(oldpath, newpath)
            if os.path.islink(oldpath):
                print(os.path.readlink(oldpath))
            os.lchown(newpath, new_uid, new_gid)
            if os.path.isdir(oldpath):
                os.rmdir(oldpath)


                




if __name__ == "__main__":
    main(*sys.argv[1:])
