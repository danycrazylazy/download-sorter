from pathlib import Path
import json
import shutil
import sys

SOURCE = Path.home() / "Downloads"
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "sort_log.json"
DRY_RUN = False


def load_log():
    if not LOG_FILE.exists():
        return {"moves": [], "dirs": []}
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "moves" not in data or "dirs" not in data:
                return {"moves": [], "dirs": []}
            return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"лог недоступен: {e}")
        return {"moves": [], "dirs": []}


def save_log(log):
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"не могу сохранить лог: {e}")


def unique_path(path, reserved):
    if not path.exists() and path not in reserved:
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists() and candidate not in reserved:
            return candidate
        i += 1


def sort_files():
    if not SOURCE.is_dir():
        print(f"папка {SOURCE.resolve()} не найдена")
        return

    log = load_log()
    reserved = set()
    done = skipped = failed = 0

    for f in sorted(SOURCE.iterdir()):
        if (
            not f.is_file()
            or f.is_symlink()
            or f.name.startswith(".")
            or f.name == LOG_FILE.name
        ):
            skipped += 1
            continue

        ext = f.suffix.lower().lstrip(".") or "no_extension"
        target_dir = SOURCE / ext

        if target_dir.exists() and not target_dir.is_dir():
            print(f"пропуск {f.name}: {target_dir} занято файлом")
            failed += 1
            continue

        dst = unique_path(target_dir / f.name, reserved)

        try:
            if DRY_RUN:
                print(f"[dry] {f.name} -> {dst}")
            else:
                if not target_dir.exists():
                    target_dir.mkdir()
                    if str(target_dir) not in log["dirs"]:
                        log["dirs"].append(str(target_dir))
                shutil.move(str(f), str(dst))
                log["moves"].append({"from": str(f), "to": str(dst)})
                print(f"{f.name} -> {dst}")
        except OSError as e:
            print(f"ошибка {f.name}: {e}")
            failed += 1
            continue

        reserved.add(dst)
        done += 1

    if not DRY_RUN:
        save_log(log)

    verb = "к перемещению" if DRY_RUN else "перемещено"
    print(f"{verb}: {done}, пропущено: {skipped}, ошибок: {failed}")


def rollback():
    log = load_log()

    if not log["moves"]:
        print("откатывать нечего: лог пуст")
        return

    done = failed = 0
    remaining_moves = []

    for move in reversed(log["moves"]):
        src = Path(move["to"])
        dst = Path(move["from"])

        if not src.exists():
            print(f"пропуск {src.name}: файл уже не там")
            continue

        if dst.exists():
            print(f"пропуск {src.name}: {dst.name} уже есть в корне")
            remaining_moves.append(move)
            failed += 1
            continue

        try:
            if DRY_RUN:
                print(f"[dry] {src} -> {dst}")
            else:
                shutil.move(str(src), str(dst))
                print(f"возврат: {src.name}")
            done += 1
        except OSError as e:
            print(f"ошибка {src.name}: {e}")
            remaining_moves.append(move)
            failed += 1

    remaining_dirs = []
    if not DRY_RUN:
        for d in sorted(log["dirs"], key=len, reverse=True):
            p = Path(d)
            if not p.exists():
                continue
            try:
                p.rmdir()
                print(f"удалена папка: {p.name}")
            except OSError:
                remaining_dirs.append(d)
                print(f"папка не пуста, оставлена: {p.name}")

        save_log({"moves": remaining_moves, "dirs": remaining_dirs})

    verb = "к возврату" if DRY_RUN else "возвращено"
    print(f"{verb}: {done}, ошибок: {failed}")


def main():
    mode = "sort"
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("rollback", "undo", "откат"):
        mode = "rollback"

    if mode == "rollback":
        rollback()
    else:
        sort_files()


if __name__ == "__main__":
    main()