import re
import os

def update_overleaf():
    tex_path = os.path.join('Overleaf', 'acl_latex.tex')
    standalone_path = os.path.join('Overleaf', 'acl_latex_standalone.tex')
    
    with open(tex_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Fix duplicated text in line 213
    text = text.replace(
        "multilingual transformers (multilingual transformers (XLM-RoBERTa Base",
        "multilingual transformers (XLM-RoBERTa Base"
    )

    # 2. Fix unescaped ampersand in itemize
    text = text.replace(
        r"\item \textbf{Short-Text & OCR Applications:}",
        r"\item \textbf{Short-Text \& OCR Applications:}"
    )

    # 3. Convert all markdown **bold** to \textbf{bold}
    text = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)

    # 4. In preamble, add safety definitions for \citename if not present
    if "\\providecommand{\\citename}" not in text:
        text = text.replace(
            "\\usepackage{placeins}",
            "\\usepackage{placeins}\n\\providecommand{\\citename}[1]{#1}"
        )

    # 5. Build the 100% natbib-compatible thebibliography block
    natbib_bibitems = """\\begin{thebibliography}{28}
\\expandafter\\ifx\\csname natexlab\\endcsname\\relax\\def\\natexlab#1{#1}\\fi

\\bibitem[{Burchell et~al.(2023)Burchell, Birch, Bogoychev, and Heafield}]{burchell2023openlid}
Laurie Burchell, Alexandra Birch, Nikolay Bogoychev, and Kenneth Heafield. 2023.
\\newblock An open-source language identification tool for low-resource languages ({OpenLID}).
\\newblock In {\\em Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)}, pages 160--169.

\\bibitem[{Caswell et~al.(2020)Caswell, Shen, and Chelba}]{caswell2020language}
Isaac Caswell, Theresa Shen, and Ciprian Chelba. 2020.
\\newblock Language {ID} in the wild: Unexpected challenges on the web.
\\newblock In {\\em Proceedings of the 28th International Conference on Computational Linguistics (COLING)}, pages 5789--5805.

\\bibitem[{Chen and Guestrin(2016)}]{chen2016xgboost}
Tianqi Chen and Carlos Guestrin. 2016.
\\newblock {XGBoost}: A scalable tree boosting system.
\\newblock In {\\em Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining}, pages 785--794.

\\bibitem[{Cho et~al.(2014)Cho, van~Merri{\\"e}nboer, Gulcehre, Bahdanau, Bougares, Schwenk, and Bengio}]{cho2014learning}
Kyunghyun Cho, Bart van~Merri{\\"e}nboer, Caglar Gulcehre, Dzmitry Bahdanau, Fethi Bougares, Holger Schwenk, and Yoshua Bengio. 2014.
\\newblock Learning phrase representations using {RNN} encoder--decoder for statistical machine translation.
\\newblock In {\\em Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, pages 1724--1734.

\\bibitem[{Conneau et~al.(2020)Conneau, Khandelwal, Goyal, Chaudhary, Wenzek, Guzm{\\'a}n, Grave, Ott, Zettlemoyer, and Stoyanov}]{conneau2020unsupervised}
Alexis Conneau, Kartikay Khandelwal, Naman Goyal, Vishrav Chaudhary, Guillaume Wenzek, Francisco Guzm{\\'a}n, Edouard Grave, Myle Ott, Luke Zettlemoyer, and Veselin Stoyanov. 2020.
\\newblock Unsupervised cross-lingual representation learning at scale.
\\newblock In {\\em Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics}, pages 8440--8451.

\\bibitem[{Devlin et~al.(2019)Devlin, Chang, Lee, and Toutanova}]{devlin2019bert}
Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019.
\\newblock {BERT}: Pre-training of deep bidirectional transformers for language understanding.
\\newblock In {\\em Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)}, pages 4171--4186.

\\bibitem[{Dunn(2023)}]{dunn2023commonlid}
Jonathan Dunn. 2023.
\\newblock {CommonLID}: Language identification for massively multilingual web corpora.
\\newblock In {\\em Proceedings of the EACL Benchmark Workshop}, pages 1--10.

\\bibitem[{French(1999)}]{french1999catastrophic}
Robert~M. French. 1999.
\\newblock Catastrophic forgetting in connectionist networks.
\\newblock {\\em Trends in Cognitive Sciences}, 3(4):128--135.

\\bibitem[{Hellwig(2010)}]{hellwig2010dcs}
Oliver Hellwig. 2010.
\\newblock {DCS} - The Digital Corpus of Sanskrit.
\\newblock In {\\em Proceedings of the 17th World Sanskrit Conference}.

\\bibitem[{Goyal et~al.(2022)Goyal, Gao, Chaudhary, Chen, Wenzek, Ju, Krishnan, Riemersma, Guzm{\\'a}n, and Fan}]{goyal2022flores}
Naman Goyal, Cynthia Gao, Vishrav Chaudhary, Peng-Jen Chen, Guillaume Wenzek, Da~Ju, Sanjana Krishnan, Marc Riemersma, Francisco Guzm{\\'a}n, and Angela Fan. 2022.
\\newblock The {FLORES-101} evaluation benchmark for low-resource language translation.
\\newblock {\\em Transactions of the Association for Computational Linguistics}, 10:522--538.

\\bibitem[{Hu et~al.(2022)Hu, Shen, Wallis, Allen-Zhu, Li, Wang, Wang, and Chen}]{hu2022lora}
Edward~J. Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu~Wang, and Weizhu Chen. 2022.
\\newblock {LoRA}: Low-rank adaptation of large language models.
\\newblock In {\\em International Conference on Learning Representations (ICLR)}.

\\bibitem[{Jauhiainen et~al.(2019)Jauhiainen, Lui, Zampieri, Baldwin, and Lind{\\'e}n}]{jauhiainen2019automatic}
Tommi Jauhiainen, Marco Lui, Marcos Zampieri, Timothy Baldwin, and Krister Lind{\\'e}n. 2019.
\\newblock Automatic language identification in texts: A survey.
\\newblock {\\em Journal of Artificial Intelligence Research}, 65:675--782.

\\bibitem[{Joachims(1998)}]{joachims1998text}
Thorsten Joachims. 1998.
\\newblock Text categorization with support vector machines: Learning with many relevant features.
\\newblock In {\\em European Conference on Machine Learning (ECML)}, pages 137--142. Springer.

\\bibitem[{Joulin et~al.(2017)Joulin, Grave, Bojanowski, and Mikolov}]{joulin2017bag}
Armand Joulin, Edouard Grave, Piotr Bojanowski, and Tomas Mikolov. 2017.
\\newblock Bag of tricks for efficient text classification.
\\newblock In {\\em Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers)}, pages 427--431.

\\bibitem[{Kargaran et~al.(2023)Kargaran, Imani, Yvon, and Sch{\\"u}tze}]{kargaran2023glotlid}
Amir~Hossein Kargaran, Ayyoob Imani, Fran{\\c{c}}ois Yvon, and Hinrich Sch{\\"u}tze. 2023.
\\newblock {GlotLID}: Language identification for low-resource languages.
\\newblock In {\\em Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, pages 8779--8798.

\\bibitem[{Kirkpatrick et~al.(2017)Kirkpatrick, Pascanu, Rabinowitz, Veness, Desjardins, Rusu, Milan, Quan, Ramalho, Grabska-Barwinska, Hassabis, Rosewick, and Hadsell}]{kirkpatrick2017overcoming}
James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei~A. Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, Demis Hassabis, Claudia Rosewick, and Raia Hadsell. 2017.
\\newblock Overcoming catastrophic forgetting in neural networks.
\\newblock {\\em Proceedings of the National Academy of Sciences}, 114(13):3521--3526.

\\bibitem[{Lui and Baldwin(2012)}]{lui2012langid}
Marco Lui and Timothy Baldwin. 2012.
\\newblock {langid.py}: An off-the-shelf language identification tool.
\\newblock In {\\em Proceedings of the 50th Annual Meeting of the Association for Computational Linguistics: System Demonstrations}, pages 25--30.

\\bibitem[{McCallum and Nigam(1998)}]{mccallum1998comparison}
Andrew McCallum and Kamal Nigam. 1998.
\\newblock A comparison of event models for naive bayes text classification.
\\newblock In {\\em AAAI-98 Workshop on Learning for Text Categorization}, volume 752, pages 41--48.

\\bibitem[{McCloskey and Cohen(1989)}]{mccloskey1989catastrophic}
Michael McCloskey and Neal~J. Cohen. 1989.
\\newblock Catastrophic interference in connectionist networks: The sequential learning problem.
\\newblock {\\em Psychology of Learning and Motivation}, 24:109--165.

\\bibitem[{Mikolov et~al.(2013)Mikolov, Sutskever, Chen, Corrado, and Dean}]{mikolov2013distributed}
Tomas Mikolov, Ilya Sutskever, Kai Chen, Greg~S. Corrado, and Jeffrey Dean. 2013.
\\newblock Distributed representations of words and phrases and their compositionality.
\\newblock In {\\em Advances in Neural Information Processing Systems (NeurIPS)}, volume~26, pages 3111--3119.

\\bibitem[{NLLB Team et~al.(2022)Costa-juss{\\`a}, Cross, {\\c{C}}elebi, Elbayad, Fan, Heffernan, Kalbassi, Lam, Licht, Ma, et~al.}]{nllb2022}
{NLLB Team}, Marta~R. Costa-juss{\\`a}, James Cross, Onur {\\c{C}}elebi, Maha Elbayad, Angela Fan, Kevin Heffernan, Maraim Kalbassi, Janice Lam, Daniel Licht, Jean Ma, et~al. 2022.
\\newblock No language left behind: Scaling human-centered machine translation.
\\newblock {\\em arXiv preprint arXiv:2207.04672}.

\\bibitem[{Norman(1983)}]{norman1983pali}
Kenneth~Roy Norman. 1983.
\\newblock {\\em Pali Literature: Including the Canonical Literature in Prakrit and Sanskrit of All the Hinayana Schools of Buddhism}.
\\newblock Otto Harrassowitz, Wiesbaden.

\\bibitem[{Pedregosa et~al.(2011)Pedregosa, Varoquaux, Gramfort, Michel, Thirion, Grisel, Blondel, Prettenhofer, Weiss, Dubourg, et~al.}]{pedregosa2011scikit}
Fabian Pedregosa, Ga{\\"e}l Varoquaux, Alexandre Gramfort, Vincent Michel, Bertrand Thirion, Olivier Grisel, Mathieu Blondel, Peter Prettenhofer, Ron Weiss, Vincent Dubourg, et~al. 2011.
\\newblock Scikit-learn: Machine learning in python.
\\newblock {\\em Journal of Machine Learning Research}, 12:2825--2830.

\\bibitem[{Phillips and Davis(2009)}]{phillips2009tags}
Addison Phillips and Mark Davis. 2009.
\\newblock Tags for identifying languages. {BCP 47}, {RFC 5646}.
\\newblock Internet Engineering Task Force (IETF).

\\bibitem[{Rajan(2023)}]{rajan2023aksharamukha}
Vinodh Rajan. 2023.
\\newblock Aksharamukha: Script converter.
\\newblock \\url{https://aksharamukha.appspot.com}.

\\bibitem[{Thoma(2018)}]{thoma2018wili}
Martin Thoma. 2018.
\\newblock {WiLI-2018} -- a benchmark dataset for language identification.
\\newblock {\\em arXiv preprint arXiv:1801.07779}.

\\bibitem[{Welgama et~al.(2021)Welgama, Fernando, and Weerasinghe}]{welgama2021sidiac}
Viraji Welgama, Sandun Fernando, and Ruvan Weerasinghe. 2021.
\\newblock {SiDiaC-v.2.0}: An annotated digitised corpus of historical texts in {Sinhala} script.
\\newblock In {\\em Proceedings of the International Conference on Asian Language Processing (IALP)}, pages 140--145.

\\bibitem[{Zhang et~al.(2015)Zhang, Zhao, and LeCun}]{zhang2015character}
Xiang Zhang, Junbo Zhao, and Yann LeCun. 2015.
\\newblock Character-level convolutional networks for text classification.
\\newblock In {\\em Advances in Neural Information Processing Systems (NeurIPS)}, volume~28, pages 649--657.

\\end{thebibliography}"""

    # Replace manual thebibliography with \bibliography{custom} for official Overleaf
    pattern = re.compile(r'\\section\*\{References\}\s*\\begin\{thebibliography\}\{27\}.*?\\end\{thebibliography\}', re.DOTALL)
    
    official_ref_block = """% Entries for the entire Anthology, followed by custom entries
\\bibliography{custom}"""

    if '\\bibliography{custom}' not in text:
        text_official = pattern.sub(lambda m: official_ref_block, text)
        text_standalone = pattern.sub(lambda m: natbib_bibitems, text)
    else:
        text_official = text
        text_standalone = text.replace(official_ref_block, natbib_bibitems)

    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(text_official)
    print(f"Updated {tex_path} successfully!")

    with open(standalone_path, 'w', encoding='utf-8') as f:
        f.write(text_standalone)
    print(f"Created {standalone_path} successfully!")

if __name__ == '__main__':
    update_overleaf()
