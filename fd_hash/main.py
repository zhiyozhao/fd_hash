import os
import os.path as osp
import json
import hashlib
import click

FDHASH_FILE = ".fdhash"
ALGO = "sha1"


def read_by_chunk(file_path, chunk_size=4096):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                return
            yield chunk


def gen_(root_path, name_only):
    if not osp.islink(root_path) and osp.isdir(root_path):
        root_node = {}
        for name in os.listdir(root_path):
            if name.startswith("."):
                continue
            path = osp.join(root_path, name)
            root_node[name] = gen_(path, name_only)

        return root_node
    elif osp.islink(root_path):
        res = None
        if not name_only:
            content = bytes(os.readlink(root_path), encoding="utf-8")
            res = getattr(hashlib, ALGO)(content).hexdigest()
    elif osp.isfile(root_path):
        res = None
        if not name_only:
            hasher = getattr(hashlib, ALGO)()
            chunks = read_by_chunk(root_path)
            for chunk in chunks:
                hasher.update(chunk)
            res = hasher.hexdigest()
    else:
        assert (
            False
        ), f"{root_path} with special file type (not symlink, file or directory)"

    return res


def check_(root_path, org, cur, name_only):
    if not osp.islink(root_path) and osp.isdir(root_path):
        org_names = set([key for key in org.keys() if not key.startswith(".")])
        cur_names = set([key for key in cur.keys() if not key.startswith(".")])
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
            check_(path, org[name], cur[name], name_only)
    elif osp.islink(root_path) or osp.isfile(root_path):
        if not name_only and org != cur:
            print(f"c: {root_path}")
    else:
        assert (
            False
        ), f"{root_path} with special file type (not symlink, file or directory)"


@click.command()
@click.option("-n", "--name-only", is_flag=True, help="Ignoring the file content.")
@click.argument("directory")
def gen(directory, name_only):
    """Generate folder content description file"""
    file_tree = gen_(directory, name_only)
    des_path = osp.join(directory, FDHASH_FILE)
    with open(des_path, "wt") as f:
        json.dump(file_tree, f, ensure_ascii=False, indent=2)


@click.command()
@click.option("-n", "--name-only", is_flag=True, help="Ignoring the file content.")
@click.argument("directory")
def check(directory, name_only):
    """Check against folder content description file"""
    des_path = osp.join(directory, FDHASH_FILE)
    with open(des_path, "rt") as f:
        org_tree = json.load(f)
    cur_tree = gen_(directory, name_only)
    check_(directory, org_tree, cur_tree, name_only)


@click.group()
def fdhash():
    """Track folder content by generating hash descriptions"""
    pass


fdhash.add_command(gen)
fdhash.add_command(check)
