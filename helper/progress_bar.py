from tqdm import tqdm
"""
References to use tqdm with paramiko:
https://github.com/tqdm/tqdm/issues/311
https://raw.githubusercontent.com/tqdm/tqdm/master/examples/tqdm_wget.py

The get and put method of sftp client in paramiko supports callback. The callback function format is like this
func(int, int), the first int is bytes for blocks transferred, the second int is blocks to be transferred (total).
"""


def progress_bar(*args, **kwargs):
    pbar = tqdm(*args, **kwargs)
    last = [0]  # last block transferred

    def progress_wrapper(transferred, to_be_transferred):
        pbar.total = int(to_be_transferred)
        pbar.update(int(transferred - last[0]))  # transferred subtract from last block transferred
        last[0] = transferred  # update last block transferred
    return progress_wrapper, pbar
