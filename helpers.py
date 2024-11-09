import linecache
import os
import tracemalloc

import psutil

cwd = os.getcwd()


def print_current_memory_usage(label):
    python_process = psutil.Process(os.getpid())
    process_memory = python_process.memory_info()[0] / 1024**2
    current_memory, peak_memory = tracemalloc.get_traced_memory()

    current_memory /= 1024**2
    peak_memory /= 1024**2

    print(
        label,
        " - process memory: %.1f Mib" % (process_memory,),
        " - trace_malloc:",
        "current=%.1f MiB, peak=%.1f MiB" % (current_memory, peak_memory),
    )


def print_tracemalloc_top():
    snapshot = tracemalloc.take_snapshot()
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        )
    )
    top_stats = snapshot.statistics("lineno")

    print()
    print("Top 10 lines for memory allocation")
    for index, stat in enumerate(top_stats[:10], 1):
        frame = stat.traceback[0]
        print(
            "#%s: %s:%s: %.1f MiB"
            % (
                index,
                frame.filename.replace(f"{cwd}/", "./"),
                frame.lineno,
                stat.size / (1024**2),
            )
        )
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print("    %s" % line)

    other = top_stats[10:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f MiB" % (len(other), size / (1024**2)))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f MiB" % (total / (1024**2)))
