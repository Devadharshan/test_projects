import os
import threading
import heapq
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor

# ==== CONFIGURATION ====
# Add your network shares or local directories here
SHARES = [
    r"\\server1\share1",
    r"\\server2\share2",
    r"D:\data"
]

WORKERS = 12          # Number of threads to use
TOP_FILES = 30        # Number of largest files to display
TOP_FOLDERS = 20      # Number of largest folders to display
MIN_FILE_SIZE = 1     # Minimum size (in bytes) to consider
FOLLOW_SYMLINKS = False

# ==== UTILITIES ====
def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


class FastDiskScanner:
    def __init__(self, roots, workers=8, top_files=50, min_size=1, follow_symlinks=False):
        self.roots = [os.path.abspath(r) for r in roots]
        self.workers = workers
        self.top_files_n = top_files
        self.min_size = min_size
        self.follow_symlinks = follow_symlinks

        self._top_files_heap = []  # (size, path)
        self._heap_lock = threading.Lock()

        self._dir_immediate_sizes = defaultdict(int)
        self._dir_lock = threading.Lock()

        self._files_count = 0
        self._dirs_count = 0
        self._errors = 0

    def _maybe_push_file(self, size, path):
        if size < self.min_size:
            return
        with self._heap_lock:
            if len(self._top_files_heap) < self.top_files_n:
                heapq.heappush(self._top_files_heap, (size, path))
            else:
                if size > self._top_files_heap[0][0]:
                    heapq.heapreplace(self._top_files_heap, (size, path))

    def _process_dir(self, start_dir, dir_queue):
        try:
            with os.scandir(start_dir) as it:
                immediate_sum = 0
                for entry in it:
                    try:
                        if entry.is_symlink() and not self.follow_symlinks:
                            continue

                        if entry.is_file(follow_symlinks=self.follow_symlinks):
                            size = entry.stat(follow_symlinks=self.follow_symlinks).st_size
                            immediate_sum += size
                            self._maybe_push_file(size, entry.path)
                            self._files_count += 1

                        elif entry.is_dir(follow_symlinks=self.follow_symlinks):
                            dir_queue.append(entry.path)
                            self._dirs_count += 1
                    except Exception:
                        self._errors += 1
                if immediate_sum:
                    with self._dir_lock:
                        self._dir_immediate_sizes[start_dir] += immediate_sum
        except Exception:
            self._errors += 1

    def scan(self):
        dir_queue = deque()
        for r in self.roots:
            if os.path.isdir(r):
                dir_queue.append(r)
            elif os.path.isfile(r):
                size = os.path.getsize(r)
                self._maybe_push_file(size, r)
                parent = os.path.dirname(r)
                with self._dir_lock:
                    self._dir_immediate_sizes[parent] += size
                self._files_count += 1

        def worker():
            while True:
                try:
                    start_dir = dir_queue.popleft()
                except IndexError:
                    break
                self._process_dir(start_dir, dir_queue)

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futures = [ex.submit(worker) for _ in range(self.workers)]

        top_files = sorted(self._top_files_heap, key=lambda x: x[0], reverse=True)
        top_folders = self._aggregate_dir_sizes()
        return top_files, top_folders

    def _aggregate_dir_sizes(self):
        sizes = dict(self._dir_immediate_sizes)
        all_dirs = set(sizes.keys())
        for d in list(all_dirs):
            p = d
            while True:
                parent = os.path.dirname(p)
                if not parent or parent == p:
                    break
                sizes.setdefault(parent, 0)
                p = parent

        dirs_sorted = sorted(sizes.keys(), key=lambda p: p.count(os.sep), reverse=True)
        for d in dirs_sorted:
            parent = os.path.dirname(d)
            if parent and parent != d:
                sizes[parent] = sizes.get(parent, 0) + sizes.get(d, 0)

        result = [(s, d) for d, s in sizes.items() if any(d.startswith(r) for r in self.roots)]
        result.sort(reverse=True, key=lambda x: x[0])
        return result


# ==== MAIN ====
def main():
    print(f"Scanning {len(SHARES)} shares with {WORKERS} workers...\n")
    scanner = FastDiskScanner(SHARES, WORKERS, TOP_FILES, MIN_FILE_SIZE, FOLLOW_SYMLINKS)
    top_files, top_folders = scanner.scan()

    print("\nTop Files:")
    for i, (size, path) in enumerate(top_files[:TOP_FILES], 1):
        print(f"{i:3}. {human_size(size):>10}  {path}")

    print("\nTop Folders:")
    for i, (size, path) in enumerate(top_folders[:TOP_FOLDERS], 1):
        print(f"{i:3}. {human_size(size):>10}  {path}")

    print("\nScan complete!")


if __name__ == "__main__":
    main()
