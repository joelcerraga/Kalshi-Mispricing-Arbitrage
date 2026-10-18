"""Compile the self-contained A4 paper source with XeLaTeX, without refitting models."""
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent

def main():
    with tempfile.TemporaryDirectory(prefix='kalshi-microstructure-paper-') as work:
        work=Path(work)
        for source in HERE.glob('*.tex'):
            shutil.copy2(source,work/source.name)
        for name in ['generated','figures','code']:
            shutil.copytree(HERE/name,work/name)
        for i in range(4):
            completed=subprocess.run(
                ['xelatex','-interaction=nonstopmode','-halt-on-error','main.tex'],
                cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
            )
            if completed.returncode:
                raise RuntimeError(completed.stdout[-6000:])
        log=(work/'main.log').read_text()
        errors=[word for word in ['Overfull','undefined','Missing character','LaTeX Font Warning'] if word in log]
        for name in ['main.aux','main.toc','main.lof','main.lot','main.loe','main.loc','main.log']:
            shutil.copy2(work/name,HERE/name)
        if errors:
            shutil.copy2(work/'main.pdf',HERE/'paper-proof.pdf')
            raise RuntimeError('Typesetting review needed: '+', '.join(errors))
        target=HERE/'Kalshi-Mispricing-and-Arbitrage-Final-Paper.pdf'
        staging=target.with_suffix('.pdf.partial')
        shutil.copy2(work/'main.pdf',staging)
        staging.replace(target)
    print(target)

if __name__=='__main__':
    main()
