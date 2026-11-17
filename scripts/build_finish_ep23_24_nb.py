"""Build the official finishing notebook for Track B (Epochs 23-24)."""
import json
from pathlib import Path
import shutil

REPO_ROOT = Path('/home/tinkerer/Desktop/ADA')
NB_OUT = REPO_ROOT / 'colab' / 'trackB_official_finish_ep23_24_kaggle.ipynb'
PUSH_DIR = REPO_ROOT / '.task-data' / 'kpush_finish_23_24'
PUSH_DIR.mkdir(parents=True, exist_ok=True)

CELLS = []

CELLS.append(('markdown', r"""# Track B - Resuming Official Retrain: Epochs 23 & 24 + Validation & Final Compilation (Kaggle 2xT4)

This notebook resumes the **official DOTA v2.0 retrain** from clean `epoch_22.pth` (trained on official 18-class dataset with difficulty flags preserved).
It completes the full planned **2x schedule (24 epochs)**:
1. Resumes from `epoch_22.pth`
2. Trains **Epoch 23 and Epoch 24** using distributed multi-GPU training (2 x Tesla T4)
3. Runs the **official validation at Epoch 24** on all 7,122 patches (81,048 instances)
4. Computes extended diagnostic metrics via `scripts/run_track_eval.py` (mAP50, AP75, mAP50-95, F1-optimal threshold, class-agnostic AP50, classification gap, small/medium/large scale AP50, orientation error)
5. Compiles comparative benchmarks (Epoch 24 vs Epoch 22 vs Track A vs Target Reference)
6. Packages all checkpoints, logs, scalars, and reports into `/kaggle/working/ada_trackB_official_ep24` with SHA-256 manifest.
"""))

CELLS.append(('code', r"""#@title 1 - Environment: GPU, repo, disk, paths { display-mode: "form" }
import subprocess, sys, os, re, json
from pathlib import Path

BASE = Path('/tmp/ada')
REPO = BASE / 'ADA'
DATA = Path('/tmp/data')
VENV = Path('/tmp/mmrotate_venv')
WORK = Path('/kaggle/working/work_dirs/trackB_official_ep23-24')
OUT  = Path('/kaggle/working/ada_trackB_official_ep24')
COMMIT = '8cc6b780d0f71192173150c6fa11514139dfeac8'

os.environ['MPLBACKEND'] = 'Agg'

print(subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.total',
                      '--format=csv,noheader'], capture_output=True, text=True).stdout.strip())
print('system python', sys.version.split()[0])
print(subprocess.run(['df', '-BG', '/tmp', '/kaggle/working'], capture_output=True, text=True).stdout)

for p in (BASE, DATA, WORK, OUT, OUT / 'logs', OUT / 'checkpoints', OUT / 'eval_test'):
    p.mkdir(parents=True, exist_ok=True)

# Link /content/data to /tmp/data for path consistency
Path('/content').mkdir(parents=True, exist_ok=True)
subprocess.run(['rm', '-rf', '/content/data'])
Path('/content/data').symlink_to(DATA)
print('/content/data ->', Path('/content/data').resolve())

if not (REPO / 'scripts').is_dir():
    subprocess.run(['git', 'clone', '-q',
                    'https://github.com/Lion4467cat/dotav2-obb-benchmark.git', str(REPO)], check=True)
subprocess.run(['git', '-C', str(REPO), 'fetch', '-q', 'origin'], check=True)
subprocess.run(['git', '-C', str(REPO), 'checkout', '-q', COMMIT], check=True)
print('repo at', subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'],
                                capture_output=True, text=True).stdout.strip())
n_gpu = len(subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True).stdout.splitlines())
print('GPUs visible:', n_gpu)
assert n_gpu >= 1, 'No GPU detected: please enable the T4 x2 accelerator in notebook settings'
"""))

CELLS.append(('code', r"""#@title 2 - Provision the Python 3.11 venv with the pinned OpenMMLab stack { display-mode: "form" }
import subprocess, time, os
from pathlib import Path

CHILD_ENV = dict(os.environ)
CHILD_ENV['MPLBACKEND'] = 'Agg'

if (VENV / 'bin' / 'python').is_file():
    print('venv already present at', VENV)
else:
    t0 = time.time()
    p = subprocess.Popen(['bash', str(REPO / 'scripts' / 'setup_colab.sh'), str(REPO), str(VENV)],
                         env=CHILD_ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    for line in p.stdout:
        print(line, end='', flush=True)
    p.wait()
    print()
    print('setup exit', p.returncode, 'after', round((time.time() - t0) / 60, 1), 'min')
    assert p.returncode == 0, 'setup_colab.sh failed'
print('venv python', (VENV / 'bin' / 'python').resolve())
"""))

CELLS.append(('code', r"""#@title 3 - Verify the venv, discover epoch_22.pth, apply mmrotate patches { display-mode: "form" }
import subprocess, os, re, shutil
from pathlib import Path

PY = VENV / 'bin' / 'python'

PROBE = '''
import torch, mmcv, mmengine, mmdet, os, mmrotate
print('torch', torch.__version__, '| cuda', torch.cuda.is_available(), '|', torch.version.cuda)
print('device count', torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print('  gpu', i, torch.cuda.get_device_name(i))
print('mmcv', mmcv.__version__, '| mmengine', mmengine.__version__, '| mmdet', mmdet.__version__)
print('mmrotate', os.path.dirname(mmrotate.__file__))
'''
r = subprocess.run([str(PY), '-c', PROBE], capture_output=True, text=True)
print(r.stdout)
assert r.returncode == 0, r.stderr[-2000:]

PATCH = '''
import sys
from pathlib import Path
sys.path.insert(0, 'REPO')
from scripts.run_kaggle import patch_gaussian_dist_loss, patch_rotate_iou2d_calculator
root = Path('REPO')
patch_gaussian_dist_loss(root)
patch_rotate_iou2d_calculator(root)
'''.replace('REPO', str(REPO))
r = subprocess.run([str(PY), '-c', PATCH], capture_output=True, text=True)
print(r.stdout.strip())
assert r.returncode == 0, r.stderr[-2000:]

# ---- Locate epoch_22.pth checkpoint ----
CKPT22 = None
# Option A: Check /kaggle/input (mounted kernel sources)
INP = Path('/kaggle/input')
candidates = list(INP.rglob('*epoch_22*.pth'))
if candidates:
    for c in candidates:
        if c.stat().st_size > 700e6:
            CKPT22 = c
            print('Found epoch_22.pth in /kaggle/input:', CKPT22)
            break

# Option B: Check /kaggle/working
if CKPT22 is None:
    candidates = list(Path('/kaggle/working').rglob('*epoch_22*.pth'))
    for c in candidates:
        if c.stat().st_size > 700e6:
            CKPT22 = c
            print('Found epoch_22.pth in /kaggle/working:', CKPT22)
            break

# Option C: Download the epoch_22 dataset via Kaggle API if not mounted
if CKPT22 is None:
    print('Attempting to download epoch_22.pth via Kaggle API...')
    dl_dir = Path('/tmp/dl_ckpt22')
    dl_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(['kaggle', 'datasets', 'download', '-d', 'bhaghwanss/ada-trackb-epoch22', '-p', str(dl_dir), '--unzip'],
                   capture_output=True, text=True)
    candidates = list(dl_dir.rglob('*epoch_22*.pth'))
    for c in candidates:
        if c.stat().st_size > 700e6:
            CKPT22 = c
            print('Downloaded epoch_22.pth:', CKPT22)
            break

assert CKPT22 is not None and CKPT22.is_file(), (
    'Could not locate epoch_22.pth! Please ensure the ada-trackb-epoch22 dataset is attached as an input '
    'or epoch_22.pth is available in /kaggle/input.'
)

# Stage checkpoint to /tmp/epoch_22.pth
STAGE_CKPT = Path('/tmp/epoch_22.pth')
if not STAGE_CKPT.is_file() or STAGE_CKPT.stat().st_size != CKPT22.stat().st_size:
    shutil.copy2(CKPT22, STAGE_CKPT)
print('Staged epoch_22 checkpoint ->', STAGE_CKPT, round(STAGE_CKPT.stat().st_size / 1e6), 'MB')
"""))

CELLS.append(('code', r"""#@title 4 - Official DOTA v2.0 Dataset Acquisition & 1024/200 Tiling { display-mode: "form" }
import subprocess, time, os, shutil as _sh
from collections import Counter
from pathlib import Path

SPLIT = DATA / 'split_ss_dotav2'
RAW = DATA / 'dotav2_raw'
CACHE = DATA / 'raw_archives'
PY = VENV / 'bin' / 'python'

def sh(cmd, cwd=None):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    p = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None)
    assert p.returncode == 0, 'command failed: ' + ' '.join(str(c) for c in cmd)

def _free(paths):
    for p in paths:
        try:
            if p.is_dir():
                _sh.rmtree(p, ignore_errors=True)
            elif p.is_file():
                p.unlink()
        except OSError:
            pass

t0 = time.time()
have_patches = (
    (SPLIT / 'train' / 'annfiles').is_dir()
    and len(list((SPLIT / 'train' / 'images').glob('*.png'))) >= 20000
    and (SPLIT / 'val' / 'annfiles').is_dir()
    and len(list((SPLIT / 'val' / 'images').glob('*.png'))) >= 7000
)

if not have_patches:
    print('Downloading official DOTA v2.0 dataset (HuggingFace: isaaccorley/dota)...')
    sh([PY, REPO / 'scripts' / 'download_dotav2.py', '--source', 'huggingface',
        '--cache-dir', CACHE, '--out-dir', RAW], cwd=REPO)
    _free([RAW / '_extracted', *list(CACHE.rglob('*.tar.gz')), *list(CACHE.rglob('*.zip'))])

    for split, url in (
        ('train', 'https://huggingface.co/datasets/isaaccorley/dota/resolve/main/dotav1.0_images_train.tar.gz'),
        ('val',   'https://huggingface.co/datasets/isaaccorley/dota/resolve/main/dotav1.0_images_val.tar.gz'),
    ):
        arc = CACHE / split / url.rsplit('/', 1)[-1]
        if not arc.is_file():
            sh(['curl', '-sL', '--retry', '3', '-o', str(arc), url])
        tmp = CACHE / ('_v1_' + split)
        _sh.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        sh(['tar', 'xzf', str(arc), '-C', str(tmp)])
        imgdirs = [p for p in tmp.rglob('images') if p.is_dir()]
        best = max(imgdirs, key=lambda p: len(list(p.glob('*.png'))))
        (RAW / split / 'images').mkdir(parents=True, exist_ok=True)
        n = 0
        for f in best.glob('*.png'):
            dst = RAW / split / 'images' / f.name
            if not dst.exists():
                try:
                    os.link(f, dst)
                except OSError:
                    _sh.copy2(f, dst)
                n += 1
        print('v1.0', split, 'images merged:', n)
        _free([tmp, arc])

    _driver = Path('/tmp/tile_one_split.py')
    _driver.write_text(
        'import sys, importlib.util\n'
        'from pathlib import Path\n'
        'spec = importlib.util.spec_from_file_location("_pd", sys.argv[1])\n'
        'pd = importlib.util.module_from_spec(spec); spec.loader.exec_module(pd)\n'
        'raw, splitdir, mmrotate, split = Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), sys.argv[5]\n'
        'src = raw / split; save = splitdir / split\n'
        'import shutil as _sh\n'
        'if save.exists(): _sh.rmtree(save)\n'
        'cfg = pd.build_split_config([str(src / "images")], [str(src / "labelTxt")], save, 1024, 200, 4)\n'
        'pd.run_img_split(mmrotate, cfg)\n'
        'print("[tile]", split, "patches", len(list((save / "images").glob("*.png"))))\n'
    )
    for split in ('train', 'val'):
        sh([PY, _driver, REPO / 'scripts' / 'prepare_dotav2_patches.py', RAW, SPLIT,
            REPO / 'mmrotate', split], cwd=REPO)
        _free([RAW / split / 'images'])

print('Patches ready in', round((time.time() - t0) / 60, 1), 'min')
n_tr = len(list((SPLIT / 'train' / 'images').glob('*.png')))
n_va = len(list((SPLIT / 'val' / 'images').glob('*.png')))
print(f'Train patches: {n_tr} (expected 24,151) | Val patches: {n_va} (expected 7,122)')
assert n_tr >= 24000 and n_va == 7122, 'Dataset patch count mismatch!'
"""))

CELLS.append(('code', r"""#@title 5 - TRAIN Epochs 23 and 24 on 2 x T4 GPUs { display-mode: "form" }
import subprocess, time, os, shutil
from pathlib import Path

PY = VENV / 'bin' / 'python'
TORCHRUN = VENV / 'bin' / 'torchrun'
STAGE_CKPT = Path('/tmp/epoch_22.pth')

# Extract base configuration directly from the canonical epoch 22 checkpoint
CFG_META = WORK / 'ckpt_meta_cfg.py'
code = (
    "import torch, pathlib\n"
    f"ck = torch.load('{STAGE_CKPT}', map_location='cpu')\n"
    "cfg_str = ck['meta']['cfg']\n"
    f"pathlib.Path('{CFG_META}').write_text(cfg_str)\n"
    "print('Config extracted, length:', len(cfg_str))\n"
)
subprocess.run([str(PY), '-c', code], check=True)

TRAIN_CFG = WORK / 'train_cfg_ep23_24.py'
base_cfg = CFG_META.read_text()

# Ensure resume, val_interval=2 (validating on epoch 24), and proper output paths
extra_cfg = f'''
# ---- Resumption Overrides for Epochs 23-24 ----
work_dir = '{WORK}'
resume = True
load_from = '{STAGE_CKPT}'
train_dataloader['batch_size'] = 1
optim_wrapper['accumulative_counts'] = 4
train_cfg['max_epochs'] = 24
train_cfg['val_interval'] = 2
default_hooks['checkpoint'].update(dict(interval=1, max_keep_ckpts=3, save_best='dota/mAP', out_dir='{WORK}'))
'''
TRAIN_CFG.write_text(base_cfg + extra_cfg)
print('Training config generated ->', TRAIN_CFG)

# Seed MMEngine last_checkpoint
(WORK / 'last_checkpoint').write_text(str(STAGE_CKPT))
print('Seeded last_checkpoint ->', (WORK / 'last_checkpoint').read_text())

env = dict(os.environ)
env['MPLBACKEND'] = 'Agg'
env['PYTHONPATH'] = f"{REPO}:{REPO / 'mmrotate'}:{env.get('PYTHONPATH', '')}"
env['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'

cmd = [
    str(TORCHRUN), '--nproc_per_node=2',
    str(REPO / 'mmrotate' / 'tools' / 'train.py'), str(TRAIN_CFG),
    '--work-dir', str(WORK), '--resume', '--launcher', 'pytorch'
]
print('Starting distributed training for Epochs 23 & 24...')
print('+', ' '.join(cmd))

LOG_PATH = WORK / 'train_ep23_24_stdout.log'
t0 = time.time()
with open(LOG_PATH, 'w') as log_file:
    p = subprocess.Popen(cmd, cwd=str(REPO), env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in p.stdout:
        print(line, end='', flush=True)
        log_file.write(line)
        log_file.flush()
    p.wait()

elapsed_h = (time.time() - t0) / 3600.0
print(f'Training finished with return code {p.returncode} after {elapsed_h:.2f} hours.')
assert p.returncode == 0, 'Training run failed! Please check train_ep23_24_stdout.log'

print('Checkpoints in work directory:')
for ck in sorted(WORK.glob('*.pth')):
    print('  ', ck.name, round(ck.stat().st_size / 1e6), 'MB')
"""))

CELLS.append(('code', r"""#@title 6 - Official Validation & Extended Metrics Evaluation on Epoch 24 { display-mode: "form" }
import subprocess, json, os, time, shutil
from pathlib import Path

PY = VENV / 'bin' / 'python'

# Select the best or final epoch 24 checkpoint
candidates = sorted(WORK.glob('best_dota_mAP_epoch_*.pth'))
if not candidates:
    candidates = sorted(WORK.glob('epoch_*.pth'), key=lambda p: int(p.stem.split('_')[-1]) if p.stem.split('_')[-1].isdigit() else -1)
assert candidates, 'No checkpoint found in work directory!'
FINAL_CKPT = candidates[-1]
print('Evaluating checkpoint:', FINAL_CKPT, round(FINAL_CKPT.stat().st_size / 1e6), 'MB')

EVAL_DIR = WORK / 'eval_test'
EVAL_DIR.mkdir(parents=True, exist_ok=True)

EVAL_CFG = WORK / 'eval_cfg.py'
extra = f'''
launcher = 'none'
resume = False
load_from = '{FINAL_CKPT}'
work_dir = '{EVAL_DIR}'
'''
EVAL_CFG.write_text((WORK / 'ckpt_meta_cfg.py').read_text() + extra)

env = dict(os.environ)
env['MPLBACKEND'] = 'Agg'
env['PYTHONPATH'] = f"{REPO}:{REPO / 'mmrotate'}:{env.get('PYTHONPATH', '')}"
env['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'

cmd = [
    str(PY), str(REPO / 'scripts' / 'run_track_eval.py'),
    '--config', str(EVAL_CFG),
    '--work-dir', str(WORK),
    '--checkpoint', str(FINAL_CKPT),
    '--ann-dir', str(SPLIT / 'val' / 'annfiles'),
    '--batch-size', '1'
]
print('Running extended evaluation:')
print('+', ' '.join(cmd))
t0 = time.time()
subprocess.run(cmd, cwd=str(REPO), env=env, check=True)
print(f'Evaluation finished in {(time.time() - t0) / 60:.1f} minutes.')

EXT_METRICS = EVAL_DIR / 'extended_metrics.json'
assert EXT_METRICS.is_file(), 'extended_metrics.json was not generated!'
metrics = json.loads(EXT_METRICS.read_text())
print('=== EVALUATION SUMMARY (EPOCH 24) ===')
for k in ('num_images', 'num_gt_non_difficult', 'num_predictions', 'map50', 'ap75', 'map50_95',
          'class_agnostic_ap50', 'classification_gap_ap50'):
    print(f'  {k}: {metrics.get(k)}')
print('  f1_optimal:', metrics.get('micro_prf', {}).get('f1_optimal'))
"""))

CELLS.append(('code', r"""#@title 7 - Compile Final Benchmark Report & Package Deliverables { display-mode: "form" }
import shutil, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def cp(src, dst):
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)

print('Copying all deliverables to:', OUT)
for p in WORK.glob('*.pth'):
    cp(p, OUT / 'checkpoints' / p.name)
for p in WORK.glob('*.log'):
    cp(p, OUT / 'logs' / p.name)
for p in (WORK / 'eval_test').glob('*'):
    cp(p, OUT / 'eval_test' / p.name)
if (WORK / 'scalars.json').exists():
    cp(WORK / 'scalars.json', OUT / 'scalars.json')
cp(WORK / 'train_cfg_ep23_24.py', OUT / 'train_cfg_ep23_24.py')
cp(WORK / 'eval_cfg.py', OUT / 'eval_cfg.py')

# Read latest metrics
metrics = json.loads((OUT / 'eval_test' / 'extended_metrics.json').read_text())
opt_f1 = metrics['micro_prf']['f1_optimal']

report = f'''# DOTA v2.0 Final Benchmark Report (Official Full Run: 24 Epochs)

## Run Details
- Dataset: Official DOTA v2.0 (1,830 train / 593 val, 7,122 patches, 18 classes, difficulty flags preserved)
- Model: Oriented Faster R-CNN (ConvNeXt-S + PAFPN + Gaussian KLD loss)
- Schedule: 2x (24 Epochs complete)

## Core Metrics Comparison

| Model / Milestone | Precision (F1-opt) | Recall (F1-opt) | F1-Score | mAP50 | mAP50-95 | AP75 | Epoch |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Reference Target | 0.7430 | 0.5670 | 0.6432 | 0.5970 | 0.4210 | — | — |
| Track A (Baseline R50 1x) | 0.8157 | 0.7563 | 0.7849 | 0.6049 | 0.3146 | 0.2785 | 10 |
| Track B (Epoch 22 Milestone) | 0.8745 | 0.8313 | 0.8524 | 0.7015 | 0.4235 | 0.4553 | 22 |
| **Track B (Epoch 24 Final)** | **{opt_f1['precision']:.4f}** | **{opt_f1['recall']:.4f}** | **{opt_f1['f1']:.4f}** | **{metrics['map50']:.4f}** | **{metrics['map50_95']:.4f}** | **{metrics['ap75']:.4f}** | **24** |

## Diagnostic Metrics
- Class-Agnostic AP50: {metrics.get('class_agnostic_ap50', 0):.4f}
- Classification Gap: {metrics.get('classification_gap_ap50', 0):.4f}
- Orientation Error (Mean): {metrics.get('orientation_error', {}).get('mean_deg_all', 0):.2f}°
- Orientation Error (Median): {metrics.get('orientation_error', {}).get('median_deg_all', 0):.2f}°
- Easy GT Recall: {metrics.get('difficulty_recall', {}).get('easy_recall', 0):.4f}
- Difficult GT Recall: {metrics.get('difficulty_recall', {}).get('difficult_recall', 0):.4f}
'''
(OUT / 'final_benchmark_report_ep24.md').write_text(report)
print(report)

# Build SHA-256 Manifest
files = []
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name != 'manifest.json':
        files.append({'path': str(p.relative_to(OUT)), 'size': p.stat().st_size, 'sha256': sha256(p)})

manifest = {
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'completed_epochs': 24,
    'metrics': {
        'map50': metrics['map50'],
        'ap75': metrics['ap75'],
        'map50_95': metrics['map50_95'],
        'f1_optimal': opt_f1,
    },
    'n_files': len(files),
    'files': files,
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('Manifest saved successfully! Total files:', len(files))
"""))

# Convert to nbformat JSON
def _cell(t, s):
    c = {'cell_type': t, 'metadata': {}, 'source': [s + '\n']}
    if t == 'code':
        c['outputs'] = []
        c['execution_count'] = None
    return c

nb = {
    'cells': [_cell(t, s) for t, s in CELLS],
    'metadata': {
        'kernelspec': {
            'name': 'python3',
            'display_name': 'Python 3',
        },
        'language_info': {'name': 'python'},
        'accelerator': 'GPU',
    },
    'nbformat': 4,
    'nbformat_minor': 4,
}

NB_OUT.parent.mkdir(parents=True, exist_ok=True)
NB_OUT.write_text(json.dumps(nb, indent=1))
print('Finished building notebook ->', NB_OUT)

# Also copy into kpush_finish_23_24 with kernel metadata
shutil.copy2(NB_OUT, PUSH_DIR / 'trackB_official_finish_ep23_24_kaggle.ipynb')
meta = {
    "id": "bhaghwanss/trackb-finish-ep23-24",
    "title": "trackB finish ep23-24 (train + val + final report)",
    "code_file": "trackB_official_finish_ep23_24_kaggle.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": True,
    "enable_gpu": True,
    "enable_internet": True,
    "dataset_sources": [
        "bhaghwanss/ada-trackb-epoch22"
    ]
}
(PUSH_DIR / 'kernel-metadata.json').write_text(json.dumps(meta, indent=2))
print('Kernel metadata created in ->', PUSH_DIR / 'kernel-metadata.json')
