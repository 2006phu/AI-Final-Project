import os
import shutil
import zipfile

# Thong tin Do an Cuoi ky - Nhom 08 - TDTU
GROUP_ID = "08"
MEMBERS = [
    ("524H0121", "Le Phu"),
    ("524H0095", "Vu Giang Huy"),
    ("524H0102", "Le Hoang Minh Khoi"),
]

EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    ".git",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    ".system_generated",
    "scratch",
    "dist",
    "build",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".zip",
    ".log",
}

EXCLUDE_ROOT_FILES = {
    "package_submission.py",
    "THIET_KE_HE_THONG.md",
    "2627-HK1-AI-CK.md",
    "2627-HK1-AI-CK.pdf",
}


def should_exclude(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith("."):
            return True

    base = os.path.basename(rel_path)
    if base in EXCLUDE_ROOT_FILES:
        return True

    _, ext = os.path.splitext(base)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return True

    return False


def build_submission_zips():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "source")
    report_file = os.path.join(base_dir, "report.pdf")
    demo_file = os.path.join(base_dir, "demo.txt")

    # 1. Kiem tra cac tap tin bat buoc
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Khong tim thay thu muc source: {source_dir}")

    if not os.path.exists(demo_file):
        raise FileNotFoundError(f"Khong tim thay tap tin demo.txt: {demo_file}")

    if not os.path.exists(report_file):
        raise FileNotFoundError(
            f"[LOI NGHIEP TRONG] Khong tim thay tap tin bao cao: {report_file}!\n"
            "Yeu cau dat file bao cao nghiem tuc report.pdf vao thu muc goc truoc khi dong goi."
        )

    # Kiem tra tinh hop le cua report.pdf (khong phai file rong hoac placeholder)
    report_size_kb = os.path.getsize(report_file) / 1024.0
    if report_size_kb < 10.0:
        raise ValueError(
            f"[LOI] File report.pdf qua nho ({report_size_kb:.2f} KB), co the la file rong hoac placeholder gia!\n"
            "Vui long kiem tra lai bao cao PDF thuc te truoc khi nop."
        )

    try:
        import pypdf
        reader = pypdf.PdfReader(report_file)
        page_count = len(reader.pages)
        if page_count > 5:
            print(f"[CANH BAO] report.pdf co {page_count} trang, vuot qua gioi han 5 trang cua IEEE!")
        else:
            print(f"[XAC THUC] report.pdf hop le: {page_count} trang ({report_size_kb:.1f} KB), dap ung gioi han <= 5 trang.")
    except Exception as e:
        print(f"[THONG BAO] Khong the doc chi tiet trang PDF bang pypdf ({e}), tiep tuc kiem tra kich thuoc hop le.")

    # Thu thap danh sach tap tin trong source/
    source_files: list[tuple[str, str]] = []  # (abs_path, arcname_inside_source)
    seen_arcs = set()
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            abs_p = os.path.join(root, f)
            rel_p = os.path.relpath(abs_p, source_dir).replace("\\", "/")
            if not should_exclude(rel_p) and rel_p not in seen_arcs:
                source_files.append((abs_p, rel_p))
                seen_arcs.add(rel_p)

    # Cung them cac tap tin entrypoint o thu muc goc vao source (run.bat, run_1click.bat, run.sh)
    root_launchers = ["run.bat", "run_1click.bat", "run.sh"]
    for l_name in root_launchers:
        l_path = os.path.join(base_dir, l_name)
        if os.path.exists(l_path) and l_name not in seen_arcs:
            source_files.append((l_path, l_name))
            seen_arcs.add(l_name)

    print(f"[INFO] Da thu thap {len(source_files)} tap tin hop le trong goi source.")

    # 2. Tao goi zip cho tung thanh vien
    created_zips = []
    for mssv, name in MEMBERS:
        folder_name = f"AI_final_{GROUP_ID}_{mssv}"
        zip_name = f"{folder_name}.zip"
        zip_path = os.path.join(base_dir, zip_name)

        print(f"\n=======================================================")
        print(f"Dang dong goi cho: {name} ({mssv}) -> {zip_name}")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. report.pdf
            zf.write(report_file, arcname=f"{folder_name}/report.pdf")

            # 2. demo.txt
            zf.write(demo_file, arcname=f"{folder_name}/demo.txt")

            # 3. source/...
            for abs_path, arc_subpath in source_files:
                target_arc = f"{folder_name}/source/{arc_subpath}".replace("\\", "/")
                zf.write(abs_path, arcname=target_arc)

        zip_size_kb = os.path.getsize(zip_path) / 1024.0
        print(f"[THANH CONG] Da tao {zip_name} ({zip_size_kb:.1f} KB)")
        created_zips.append((zip_path, zip_size_kb))

    # 3. Kiem tra tinh toan ven cua cac tap tin zip da tao
    print(f"\n=======================================================")
    print("[INFO] Kiem tra tinh toan ven (Integrity verification)...")
    for z_path, size_kb in created_zips:
        with zipfile.ZipFile(z_path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                raise ValueError(f"Phat hien tap tin loi trong {z_path}: {bad_file}")
            names = zf.namelist()
            prefix = os.path.splitext(os.path.basename(z_path))[0]
            assert f"{prefix}/report.pdf" in names
            assert f"{prefix}/demo.txt" in names
            assert f"{prefix}/source/README.md" in names
            assert f"{prefix}/source/requirements.txt" in names
            assert f"{prefix}/source/requirement.txt" in names
            assert f"{prefix}/source/main.py" in names
            print(f"  [PASS] {os.path.basename(z_path)}: {len(names)} tap tin ben trong, toan ven 100%.")

    print("\n=======================================================")
    print("[HOAN TAT] DA DONG GOI XUAT SAC TOAN BO 3 BUNDLE NOP BAI!")
    print("Moi thanh vien co the nop file .zip tuong ung len he thong nop bai.")


if __name__ == "__main__":
    build_submission_zips()
