"""ree run file.ree — تشغيل برنامج REE من سطر الأوامر."""
import argparse
import json
import sys

from .engine import run_file


def main():
    parser = argparse.ArgumentParser(prog="ree", description="محرك تنفيذ لغة REE الوصفية")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="تنفيذ ملف .ree")
    run_cmd.add_argument("file", help="مسار ملف .ree")
    run_cmd.add_argument("-v", "--verbose", action="store_true", help="طباعة كل كتلة أثناء التنفيذ")
    run_cmd.add_argument("-o", "--output", help="حفظ النتائج كـ JSON في هذا المسار")

    args = parser.parse_args()

    if args.command == "run":
        ctx = run_file(args.file, verbose=args.verbose)
        printable = {k: v for k, v in ctx.items()}
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(printable, f, ensure_ascii=False, indent=2, default=str)
            print(f"تم حفظ النتائج في {args.output}")
        else:
            print(json.dumps(printable, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    sys.exit(main())
