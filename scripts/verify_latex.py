import re
import sys

def verify_file(filepath):
    print(f"\n--- Verifying {filepath} ---")
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.splitlines()
    total_open = 0
    total_close = 0
    
    for idx, line in enumerate(lines):
        clean = re.sub(r'\\.', '', line)
        if '%' in clean:
            clean = clean[:clean.index('%')]
        o = clean.count('{')
        c = clean.count('}')
        total_open += o
        total_close += c

    print(f"Total curly braces: {total_open} open, {total_close} close (balance: {total_open - total_close})")

    # Check bibliography command
    if '\\bibliography{custom}' in text:
        print("Uses official \\bibliography{custom} command: YES")
    elif '\\begin{thebibliography}' in text:
        print("Uses inline \\begin{thebibliography}: YES")

    # Check citename definition
    if '\\citename' in text:
        if '\\providecommand{\\citename}' in text or '\\newcommand{\\citename}' in text:
            print("Safe \\citename definition present: YES")
        else:
            print("WARNING: \\citename is used in document but NOT defined!")

    # Check natbib compatibility of bibitems
    bad_bibitems = []
    total_bibitems = 0
    for line in lines:
        if line.startswith('\\bibitem'):
            total_bibitems += 1
            m = re.search(r'\\bibitem\[(.*)\]\{([^}]+)\}', line)
            if m:
                opt = m.group(1)
                key = m.group(2)
                if not re.search(r'\(\d{4}\)', opt):
                    bad_bibitems.append((key, opt))
            else:
                bad_bibitems.append(('unknown', line))

    if total_bibitems > 0:
        print(f"Total \\bibitem entries: {total_bibitems}")
        print(f"Bibitems without (year) in optional arg: {len(bad_bibitems)}")
        if bad_bibitems:
            print("Sample bad bibitems:", bad_bibitems[:3])
        else:
            print("All \\bibitem entries are 100% natbib author-year compatible: YES")

def verify():
    import os
    files_to_check = [
        'ACLV2.tex',
        os.path.join('Overleaf', 'acl_latex.tex'),
        os.path.join('Overleaf', 'acl_latex_standalone.tex')
    ]
    if os.path.exists('ACLV2_standalone.tex'):
        files_to_check.append('ACLV2_standalone.tex')

    for f in files_to_check:
        if os.path.exists(f):
            verify_file(f)

    # Check citations in acl_latex.tex against custom.bib
    with open(os.path.join('Overleaf', 'acl_latex.tex'), 'r', encoding='utf-8') as f:
        tex = f.read()
    with open(os.path.join('Overleaf', 'custom.bib'), 'r', encoding='utf-8') as f:
        bib = f.read()

    tex_cites = set()
    for m in re.finditer(r'\\cite[a-z]*\{([^}]+)\}', tex):
        for key in m.group(1).split(','):
            tex_cites.add(key.strip())

    bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib))
    print(f"\n--- Citation Cross-Check ---")
    print(f"Total unique citations in text: {len(tex_cites)}")
    print(f"Total entries in custom.bib: {len(bib_keys)}")
    missing = tex_cites - bib_keys
    if missing:
        print(f"ERROR: Citations missing from custom.bib: {missing}")
    else:
        print(f"All {len(tex_cites)} citations are present in custom.bib: YES (100% match!)")

if __name__ == '__main__':
    verify()
