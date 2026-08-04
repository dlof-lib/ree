"""ree — واجهة سطر الأوامر لمحرك REE: run / check / repl."""
import argparse
import json
import sys

from .engine import run, run_file
from .errors import REEError
from .parser import parse


def _print_error(err: REEError) -> None:
    print(f"\033[91m{err.format()}\033[0m", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(prog="ree", description="محرك تنفيذ لغة REE الوصفية")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="تنفيذ ملف .ree")
    run_cmd.add_argument("file", help="مسار ملف .ree")
    run_cmd.add_argument("-v", "--verbose", action="store_true", help="طباعة كل كتلة أثناء التنفيذ")
    run_cmd.add_argument("-o", "--output", help="حفظ النتائج كـ JSON في هذا المسار")

    check_cmd = sub.add_parser("check", help="التحقق من صحة الصياغة دون تنفيذ فعلي")
    check_cmd.add_argument("file", help="مسار ملف .ree")

    sub.add_parser("repl", help="وضع تفاعلي لتجربة أوامر REE مباشرة")

    args = parser.parse_args()

    try:
        if args.command == "run":
            ctx = run_file(args.file, verbose=args.verbose)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(ctx, f, ensure_ascii=False, indent=2, default=str)
                print(f"تم حفظ النتائج في {args.output}")
            else:
                print(json.dumps(ctx, ensure_ascii=False, indent=2, default=str))

        elif args.command == "check":
            with open(args.file, "r", encoding="utf-8") as f:
                source = f.read()
            parse(source)
            print(f"✓ {args.file} صحيح نحويًا")

        elif args.command == "repl":
            print("REE REPL — اكتب 'exit' أو 'خروج' للإنهاء")
            buffer = ""
            while True:
                try:
                    line = input("... " if buffer else ">>> ")
                except EOFError:
                    break
                if not buffer and line.strip() in ("exit", "خروج"):
                    break
                buffer += line + "\n"
                if buffer.count("{") <= buffer.count("}"):
                    try:
                        ctx = run(buffer)
                        print(json.dumps(ctx, ensure_ascii=False, indent=2, default=str))
                    except REEError as e:
                        _print_error(e)
                    buffer = ""
        return 0
    except REEError as e:
        _print_error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
