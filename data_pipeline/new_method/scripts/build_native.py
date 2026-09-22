"""Build the bundled MIT-licensed fastText v0.9.2 continuation executable."""
from pathlib import Path
import os, shutil, subprocess, sys

def build(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    # Keep the host's executable suffix so a binary built for another OS is never reused.
    output=root/('bin/lid_native.exe' if sys.platform=='win32' else 'bin/lid_native')
    sources=sorted((root/'native/fasttext/src').glob('*.cc'))+[root/'native/continue.cc']
    if output.exists() and output.stat().st_mtime > max(p.stat().st_mtime for p in (root/'native').rglob('*') if p.is_file()):
        return output
    compiler=shutil.which(os.environ.get('CXX','g++'))
    if not compiler:
        raise RuntimeError('A C++ compiler is needed. On Ubuntu/Colab: sudo apt-get install -y g++. On Windows install MSYS2/MinGW-w64 g++ and put it on PATH, or use WSL2 or Colab.')
    output.parent.mkdir(exist_ok=True)
    # MinGW links libstdc++/libgcc/winpthread as DLLs that only resolve when MSYS2 is on
    # PATH; Python spawns the binary without it. Link them in so the exe stands alone.
    static=['-static-libgcc','-static-libstdc++','-static','-lpthread'] if sys.platform=='win32' else []
    subprocess.run([compiler,'-std=c++11','-O3','-pthread','-include','cstdint','-I'+str(root/'native/fasttext/src'),
                    *map(str,sources),'-o',str(output),*static],check=True)
    return output

if __name__=='__main__': print(build())
