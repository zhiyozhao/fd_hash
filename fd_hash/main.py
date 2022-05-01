import os
import os.path as osp
import json
import hashlib
import click

FDHASH_FILE = ".fdhash"
ALGO = "sha1"


def gen_(root_path):
    if not osp.islink(root_path) and osp.isdir(root_path):
        root_node = {}
        for name in os.listdir(root_path):
            path = osp.join(root_path, name)
            root_node[name] = gen_(path)

        return root_node
    elif osp.islink(root_path):
        content = bytes(os.readlink(root_path), encoding="utf-8")
    elif osp.isfile(root_path):
        with open(root_path, "rb") as f:
            content = f.read()
    else:
        assert (
            False
        ), f"{root_path} with special file type (not symlink, file or directory)"
    res = getattr(hashlib, ALGO)(content).hexdigest()

    return res


def check_(root_path, org, cur):
    if not osp.islink(root_path) and osp.isdir(root_path):
        org_names = set(org.keys())
        cur_names = set(cur.keys())
        insc = org_names & cur_names
        org_only = org_names - cur_names
        cur_only = cur_names - org_names
        for name in org_only:
            path = osp.join(root_path, name)
            print(f"d: {path}")
        for name in cur_only:
            path = osp.join(root_path, name)
            print(f"a: {path}")
        for name in insc:
            path = osp.join(root_path, name)
            check_(path, org[name], cur[name])
    elif osp.islink(root_path) or osp.isfile(root_path):
        if org != cur:
            print(f"c: {root_path}")
    else:
        assert (
            False
        ), f"{root_path} with special file type (not symlink, file or directory)"


@click.command()
@click.argument("directory")
def gen(directory):
    """Generate folder content description file"""
    file_tree = gen_(directory)
    des_path = osp.join(directory, FDHASH_FILE)
    with open(des_path, "wt") as f:
        json.dump(file_tree, f, ensure_ascii=False, indent=2)


@click.command()
@click.argument("directory")
def check(directory):
    """Check against folder content description file"""
    des_path = osp.join(directory, FDHASH_FILE)
    with open(des_path, "rt") as f:
        org_tree = json.load(f)
    cur_tree = gen_(directory)
    check_(directory, org_tree, cur_tree)


@click.group()
def fdhash():
    """Track folder content by generating hash descriptions"""
    pass


fdhash.add_command(gen)
fdhash.add_command(check)
