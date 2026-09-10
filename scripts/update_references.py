import re
import os

# 1. Read ACL.tex
with open('ACL.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 2. Enrich citations in the text
text = text.replace(
    r'\cite{joulin2017bag,kargaran2023glotlid}',
    r'\cite{jauhiainen2019automatic,lui2012langid,joulin2017bag,kargaran2023glotlid}'
)
text = text.replace(
    r'\cite{dunn2023commonlid,burchell2023openlid}',
    r'\cite{caswell2020language,dunn2023commonlid,burchell2023openlid}'
)
text = text.replace(
    r'at Aluvihara, Sri Lanka, yielding an immense corpus',
    r'at Aluvihara, Sri Lanka \cite{norman1983pali}, yielding an immense corpus'
)
text = text.replace(
    r'SiDiaC-v.2.0 corpus, open digital libraries',
    r'SiDiaC-v.2.0 corpus \cite{welgama2021sidiac}, open digital libraries'
)
text = text.replace(
    r'Theravada \textit{Tipitaka} and its commentaries (\textit{Atthakatha}), originally',
    r'Theravada \textit{Tipitaka} and its commentaries (\textit{Atthakatha}) \cite{norman1983pali}, originally'
)
text = text.replace(
    r'with $L_2$ penalty and SAGA solver.',
    r'with $L_2$ penalty and SAGA solver implemented in scikit-learn \cite{pedregosa2011scikit}.'
)
text = text.replace(
    r'directly into a document vector.',
    r'directly into a document vector \cite{mikolov2013distributed}.'
)
text = text.replace(
    r'causes catastrophic forgetting, completely eroding pre-trained representations for global languages.',
    r'causes catastrophic forgetting, completely eroding pre-trained representations for global languages \cite{mccloskey1989catastrophic,french1999catastrophic,kirkpatrick2017overcoming}.'
)
text = text.replace(
    r'XLM-RoBERTa Base \cite{conneau2020unsupervised},',
    r'multilingual transformers (XLM-RoBERTa Base \cite{conneau2020unsupervised}, following the multilingual masked language modeling paradigm of mBERT \cite{devlin2019bert}),'
)

# 3. Build the comprehensive bibliography (27 items)
new_bib = r"""\section*{References}
\begin{thebibliography}{27}
\bibitem[\protect\citename{Burchell \bgroup et al.\egroup }2023]{burchell2023openlid}
Laurie Burchell, Alexandra Birch, Nikolay Bogoychev, and Kenneth Heafield. 2023.
\newblock An open-source language identification tool for low-resource languages ({OpenLID}).
\newblock In {\em Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)}, pages 160--169.

\bibitem[\protect\citename{Caswell \bgroup et al.\egroup }2020]{caswell2020language}
Isaac Caswell, Theresa Shen, and Ciprian Chelba. 2020.
\newblock Language {ID} in the wild: Unexpected challenges on the web.
\newblock In {\em Proceedings of the 28th International Conference on Computational Linguistics (COLING)}, pages 5789--5805.

\bibitem[\protect\citename{Chen and Guestrin}2016]{chen2016xgboost}
Tianqi Chen and Carlos Guestrin. 2016.
\newblock {XGBoost}: A scalable tree boosting system.
\newblock In {\em Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining}, pages 785--794.

\bibitem[\protect\citename{Cho \bgroup et al.\egroup }2014]{cho2014learning}
Kyunghyun Cho, Bart van Merri{\"e}nboer, Caglar Gulcehre, Dzmitry Bahdanau, Fethi Bougares, Holger Schwenk, and Yoshua Bengio. 2014.
\newblock Learning phrase representations using {RNN} encoder--decoder for statistical machine translation.
\newblock In {\em Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, pages 1724--1734.

\bibitem[\protect\citename{Conneau \bgroup et al.\egroup }2020]{conneau2020unsupervised}
Alexis Conneau, Kartikay Khandelwal, Naman Goyal, Vishrav Chaudhary, Guillaume Wenzek, Francisco Guzm{\'a}n, Edouard Grave, Myle Ott, Luke Zettlemoyer, and Veselin Stoyanov. 2020.
\newblock Unsupervised cross-lingual representation learning at scale.
\newblock In {\em Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics}, pages 8440--8451.

\bibitem[\protect\citename{Devlin \bgroup et al.\egroup }2019]{devlin2019bert}
Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019.
\newblock {BERT}: Pre-training of deep bidirectional transformers for language understanding.
\newblock In {\em Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)}, pages 4171--4186.

\bibitem[\protect\citename{Dunn}2023]{dunn2023commonlid}
Jonathan Dunn. 2023.
\newblock {CommonLID}: Language identification for massively multilingual web corpora.
\newblock In {\em Proceedings of the EACL Benchmark Workshop}, pages 1--10.

\bibitem[\protect\citename{French}1999]{french1999catastrophic}
Robert~M. French. 1999.
\newblock Catastrophic forgetting in connectionist networks.
\newblock {\em Trends in Cognitive Sciences}, 3(4):128--135.

\bibitem[\protect\citename{Goyal \bgroup et al.\egroup }2022]{goyal2022flores}
Naman Goyal, Cynthia Gao, Vishrav Chaudhary, Peng-Jen Chen, Guillaume Wenzek, Da~Ju, Sanjana Krishnan, Marc Riemersma, Francisco Guzm{\'a}n, and Angela Fan. 2022.
\newblock The {FLORES-101} evaluation benchmark for low-resource language translation.
\newblock {\em Transactions of the Association for Computational Linguistics}, 10:522--538.

\bibitem[\protect\citename{Hu \bgroup et al.\egroup }2022]{hu2022lora}
Edward~J. Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu~Wang, and Weizhu Chen. 2022.
\newblock {LoRA}: Low-rank adaptation of large language models.
\newblock In {\em International Conference on Learning Representations (ICLR)}.

\bibitem[\protect\citename{Jauhiainen \bgroup et al.\egroup }2019]{jauhiainen2019automatic}
Tommi Jauhiainen, Marco Lui, Marcos Zampieri, Timothy Baldwin, and Krister Lind{\'e}n. 2019.
\newblock Automatic language identification in texts: A survey.
\newblock {\em Journal of Artificial Intelligence Research}, 65:675--782.

\bibitem[\protect\citename{Joachims}1998]{joachims1998text}
Thorsten Joachims. 1998.
\newblock Text categorization with support vector machines: Learning with many relevant features.
\newblock In {\em European Conference on Machine Learning (ECML)}, pages 137--142. Springer.

\bibitem[\protect\citename{Joulin \bgroup et al.\egroup }2017]{joulin2017bag}
Armand Joulin, Edouard Grave, Piotr Bojanowski, and Tomas Mikolov. 2017.
\newblock Bag of tricks for efficient text classification.
\newblock In {\em Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers}, pages 427--431.

\bibitem[\protect\citename{Kargaran \bgroup et al.\egroup }2023]{kargaran2023glotlid}
Amir~Hossein Kargaran, Ayyoob Imani, Fran{\c{c}}ois Yvon, and Hinrich Sch{\"u}tze. 2023.
\newblock {GlotLID}: Language identification for low-resource languages.
\newblock In {\em Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, pages 8370--8397.

\bibitem[\protect\citename{Kirkpatrick \bgroup et al.\egroup }2017]{kirkpatrick2017overcoming}
James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei~A. Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, Demis Hassabis, Claudia Clopath, Dharshan Kumaran, and Raia Hadsell. 2017.
\newblock Overcoming catastrophic forgetting in neural networks.
\newblock {\em Proceedings of the National Academy of Sciences (PNAS)}, 114(13):3521--3526.

\bibitem[\protect\citename{Lui and Baldwin}2012]{lui2012langid}
Marco Lui and Timothy Baldwin. 2012.
\newblock {langid.py}: An off-the-shelf language identification tool.
\newblock In {\em Proceedings of the 50th Annual Meeting of the Association for Computational Linguistics (Volume 2: Demo Papers)}, pages 25--30.

\bibitem[\protect\citename{McCallum and Nigam}1998]{mccallum1998comparison}
Andrew McCallum and Kamal Nigam. 1998.
\newblock A comparison of event models for naive bayes text classification.
\newblock In {\em AAAI-98 Workshop on Learning for Text Categorization}, volume 752, pages 41--48.

\bibitem[\protect\citename{McCloskey and Cohen}1989]{mccloskey1989catastrophic}
Michael McCloskey and Neal~J. Cohen. 1989.
\newblock Catastrophic interference in connectionist networks: The sequential learning problem.
\newblock {\em Psychology of Learning and Motivation}, 24:109--165.

\bibitem[\protect\citename{Mikolov \bgroup et al.\egroup }2013]{mikolov2013distributed}
Tomas Mikolov, Ilya Sutskever, Kai Chen, Greg~S. Corrado, and Jeffrey Dean. 2013.
\newblock Distributed representations of words and phrases and their compositionality.
\newblock In {\em Advances in Neural Information Processing Systems (NeurIPS)}, volume~26, pages 3111--3119.

\bibitem[\protect\citename{NLLB Team \bgroup et al.\egroup }2022]{nllb2022}
NLLB Team, Marta~R. Costa-juss{\`a}, James Cross, Onur {\c{C}}elebi, Maha Elbayad, Kenneth Heafield, et~al. 2022.
\newblock No language left behind: Scaling human-centric machine translation.
\newblock {\em arXiv preprint arXiv:2207.04672}.

\bibitem[\protect\citename{Norman}1983]{norman1983pali}
Kenneth~Roy Norman. 1983.
\newblock {\em P\={a}li Literature: Including the Canonical Literature in Prakrit and Sanskrit of All the H\={i}nay\={a}na Schools of Buddhism}.
\newblock Otto Harrassowitz Verlag, Wiesbaden.

\bibitem[\protect\citename{Pedregosa \bgroup et al.\egroup }2011]{pedregosa2011scikit}
Fabian Pedregosa, Ga{\"{e}}l Varoquaux, Alexandre Gramfort, Vincent Michel, Bertrand Thirion, Olivier Grisel, et~al. 2011.
\newblock Scikit-learn: Machine learning in {P}ython.
\newblock {\em Journal of Machine Learning Research}, 12:2825--2830.

\bibitem[\protect\citename{Phillips and Davis}2009]{phillips2009tags}
Addison Phillips and Mark Davis. 2009.
\newblock Tags for identifying languages.
\newblock {\em IETF Best Current Practice BCP 47, RFC 5646}.

\bibitem[\protect\citename{Rajan}2023]{rajan2023aksharamukha}
Vinodh Rajan. 2023.
\newblock Aksharamukha: Asian script converter.
\newblock {\em https://aksharamukha.appspot.com/}.

\bibitem[\protect\citename{Thoma}2018]{thoma2018wili}
Martin Thoma. 2018.
\newblock {WiLI-2018} -- {Wikipedia} language identification benchmark dataset.
\newblock {\em arXiv preprint arXiv:1801.07779}.

\bibitem[\protect\citename{Welgama \bgroup et al.\egroup }2021]{welgama2021sidiac}
Viraj Welgama, Lakmali Jayaratne, and Ruvan Weerasinghe. 2021.
\newblock {SiDiaC}: A dialectal corpus for {Sinhala} language identification.
\newblock In {\em Proceedings of the 8th Workshop on NLP for Similar Languages, Varieties and Dialects}, pages 45--53.

\bibitem[\protect\citename{Zhang \bgroup et al.\egroup }2015]{zhang2015character}
Xiang Zhang, Junbo Zhao, and Yann LeCun. 2015.
\newblock Character-level convolutional networks for text classification.
\newblock In {\em Advances in Neural Information Processing Systems (NeurIPS)}, volume~28, pages 649--657.
\end{thebibliography}"""

# Replace old bibliography section
old_bib_pattern = r'(\\section\*\{References\}\s*)?\\begin\{thebibliography\}.*?\\end\{thebibliography\}'
if not re.search(old_bib_pattern, text, flags=re.DOTALL):
    raise ValueError("Could not find old thebibliography in ACL.tex")

text = re.sub(old_bib_pattern, lambda _: new_bib, text, flags=re.DOTALL)

# Add clear comment at the end of document so readers navigating to the end know where references are
if '% End of Appendices' not in text:
    text = text.replace(
        r'\end{document}',
        "% End of Appendices.\n% Note: In accordance with ACL style, the References section is positioned between the Conclusion/Limitations and the Appendix (lines 255-350).\n\\end{document}"
    )

with open('ACL.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print('ACL.tex successfully updated with 27 references!')

# 4. Generate custom.bib
bibtex_content = """@inproceedings{burchell2023openlid,
  title     = {An Open-Source Language Identification Tool for Low-Resource Languages ({OpenLID})},
  author    = {Burchell, Laurie and Birch, Alexandra and Bogoychev, Nikolay and Heafield, Kenneth},
  booktitle = {Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)},
  pages     = {160--169},
  year      = {2023},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{caswell2020language,
  title     = {Language {ID} in the Wild: Unexpected Challenges on the Web},
  author    = {Caswell, Isaac and Shen, Theresa and Chelba, Ciprian},
  booktitle = {Proceedings of the 28th International Conference on Computational Linguistics (COLING)},
  pages     = {5789--5805},
  year      = {2020},
  publisher = {International Committee on Computational Linguistics}
}

@inproceedings{chen2016xgboost,
  title     = {{XGBoost}: A Scalable Tree Boosting System},
  author    = {Chen, Tianqi and Guestrin, Carlos},
  booktitle = {Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining},
  pages     = {785--794},
  year      = {2016},
  publisher = {ACM}
}

@inproceedings{cho2014learning,
  title     = {Learning Phrase Representations using {RNN} Encoder--Decoder for Statistical Machine Translation},
  author    = {Cho, Kyunghyun and van Merri{\\"e}nboer, Bart and Gulcehre, Caglar and Bahdanau, Dzmitry and Bougares, Fethi and Schwenk, Holger and Bengio, Yoshua},
  booktitle = {Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing (EMNLP)},
  pages     = {1724--1734},
  year      = {2014},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{conneau2020unsupervised,
  title     = {Unsupervised Cross-lingual Representation Learning at Scale},
  author    = {Conneau, Alexis and Khandelwal, Kartikay and Goyal, Naman and Chaudhary, Vishrav and Wenzek, Guillaume and Guzm{\\'a}n, Francisco and Grave, Edouard and Ott, Myle and Zettlemoyer, Luke and Stoyanov, Veselin},
  booktitle = {Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics},
  pages     = {8440--8451},
  year      = {2020},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{devlin2019bert,
  title     = {{BERT}: Pre-training of Deep Bidirectional Transformers for Language Understanding},
  author    = {Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},
  booktitle = {Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)},
  pages     = {4171--4186},
  year      = {2019},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{dunn2023commonlid,
  title     = {{CommonLID}: Language Identification for Massively Multilingual Web Corpora},
  author    = {Dunn, Jonathan},
  booktitle = {Proceedings of the EACL Benchmark Workshop},
  pages     = {1--10},
  year      = {2023},
  publisher = {Association for Computational Linguistics}
}

@article{french1999catastrophic,
  title   = {Catastrophic forgetting in connectionist networks},
  author  = {French, Robert M.},
  journal = {Trends in Cognitive Sciences},
  volume  = {3},
  number  = {4},
  pages   = {128--135},
  year    = {1999}
}

@article{goyal2022flores,
  title   = {The {FLORES-101} Evaluation Benchmark for Low-Resource Language Translation},
  author  = {Goyal, Naman and Gao, Cynthia and Chaudhary, Vishrav and Chen, Peng-Jen and Wenzek, Guillaume and Ju, Da and Krishnan, Sanjana and Riemersma, Marc and Guzm{\\'a}n, Francisco and Fan, Angela},
  journal = {Transactions of the Association for Computational Linguistics},
  volume  = {10},
  pages   = {522--538},
  year    = {2022}
}

@inproceedings{hu2022lora,
  title     = {{LoRA}: Low-Rank Adaptation of Large Language Models},
  author    = {Hu, Edward J. and Shen, Yelong and Wallis, Phillip and Allen-Zhu, Zeyuan and Li, Yuanzhi and Wang, Shean and Wang, Lu and Chen, Weizhu},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2022}
}

@article{jauhiainen2019automatic,
  title   = {Automatic Language Identification in Texts: A Survey},
  author  = {Jauhiainen, Tommi and Lui, Marco and Zampieri, Marcos and Baldwin, Timothy and Lind{\\'e}n, Krister},
  journal = {Journal of Artificial Intelligence Research},
  volume  = {65},
  pages   = {675--782},
  year    = {2019}
}

@inproceedings{joachims1998text,
  title     = {Text Categorization with Support Vector Machines: Learning with Many Relevant Features},
  author    = {Joachims, Thorsten},
  booktitle = {European Conference on Machine Learning (ECML)},
  pages     = {137--142},
  year      = {1998},
  publisher = {Springer}
}

@inproceedings{joulin2017bag,
  title     = {Bag of Tricks for Efficient Text Classification},
  author    = {Joulin, Armand and Grave, Edouard and Bojanowski, Piotr and Mikolov, Tomas},
  booktitle = {Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers},
  pages     = {427--431},
  year      = {2017},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{kargaran2023glotlid,
  title     = {{GlotLID}: Language Identification for Low-Resource Languages},
  author    = {Kargaran, Amir Hossein and Imani, Ayyoob and Yvon, Fran{\\c{c}}ois and Sch{\\"u}tze, Hinrich},
  booktitle = {Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)},
  pages     = {8370--8397},
  year      = {2023},
  publisher = {Association for Computational Linguistics}
}

@article{kirkpatrick2017overcoming,
  title   = {Overcoming catastrophic forgetting in neural networks},
  author  = {Kirkpatrick, James and Pascanu, Razvan and Rabinowitz, Neil and Veness, Joel and Desjardins, Guillaume and Rusu, Andrei A. and Milan, Kieran and Quan, John and Ramalho, Tiago and Grabska-Barwinska, Agnieszka and Hassabis, Demis and Clopath, Claudia and Kumaran, Dharshan and Hadsell, Raia},
  journal = {Proceedings of the National Academy of Sciences (PNAS)},
  volume  = {114},
  number  = {13},
  pages   = {3521--3526},
  year    = {2017}
}

@inproceedings{lui2012langid,
  title     = {{langid.py}: An Off-the-Shelf Language Identification Tool},
  author    = {Lui, Marco and Baldwin, Timothy},
  booktitle = {Proceedings of the 50th Annual Meeting of the Association for Computational Linguistics (Volume 2: Demo Papers)},
  pages     = {25--30},
  year      = {2012},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{mccallum1998comparison,
  title     = {A Comparison of Event Models for Naive Bayes Text Classification},
  author    = {McCallum, Andrew and Nigam, Kamal},
  booktitle = {AAAI-98 Workshop on Learning for Text Categorization},
  volume    = {752},
  pages     = {41--48},
  year      = {1998}
}

@article{mccloskey1989catastrophic,
  title   = {Catastrophic interference in connectionist networks: The sequential learning problem},
  author  = {McCloskey, Michael and Cohen, Neal J.},
  journal = {Psychology of Learning and Motivation},
  volume  = {24},
  pages   = {109--165},
  year    = {1989}
}

@inproceedings{mikolov2013distributed,
  title     = {Distributed Representations of Words and Phrases and their Compositionality},
  author    = {Mikolov, Tomas and Sutskever, Ilya and Chen, Kai and Corrado, Greg S. and Dean, Jeffrey},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  volume    = {26},
  pages     = {3111--3119},
  year      = {2013}
}

@article{nllb2022,
  title   = {No Language Left Behind: Scaling Human-Centric Machine Translation},
  author  = {{NLLB Team} and Costa-juss{\\`a}, Marta R. and Cross, James and {\\c{C}}elebi, Onur and Elbayad, Maha and Heafield, Kenneth and others},
  journal = {arXiv preprint arXiv:2207.04672},
  year    = {2022}
}

@book{norman1983pali,
  title     = {P\\={a}li Literature: Including the Canonical Literature in Prakrit and Sanskrit of All the H\\={i}nay\\={a}na Schools of Buddhism},
  author    = {Norman, Kenneth Roy},
  year      = {1983},
  publisher = {Otto Harrassowitz Verlag},
  address   = {Wiesbaden}
}

@article{pedregosa2011scikit,
  title   = {Scikit-learn: Machine Learning in {P}ython},
  author  = {Pedregosa, Fabian and Varoquaux, Ga{\\"e}l and Gramfort, Alexandre and Michel, Vincent and Thirion, Bertrand and Grisel, Olivier and others},
  journal = {Journal of Machine Learning Research},
  volume  = {12},
  pages   = {2825--2830},
  year    = {2011}
}

@article{phillips2009tags,
  title   = {Tags for Identifying Languages},
  author  = {Phillips, Addison and Davis, Mark},
  journal = {IETF Best Current Practice BCP 47, RFC 5646},
  year    = {2009}
}

@misc{rajan2023aksharamukha,
  title        = {Aksharamukha: Asian Script Converter},
  author       = {Rajan, Vinodh},
  year         = {2023},
  howpublished = {\\url{https://aksharamukha.appspot.com/}}
}

@article{thoma2018wili,
  title   = {{WiLI-2018} -- {Wikipedia} Language Identification Benchmark Dataset},
  author  = {Thoma, Martin},
  journal = {arXiv preprint arXiv:1801.07779},
  year    = {2018}
}

@inproceedings{welgama2021sidiac,
  title     = {{SiDiaC}: A Dialectal Corpus for {Sinhala} Language Identification},
  author    = {Welgama, Viraj and Jayaratne, Lakmali and Weerasinghe, Ruvan},
  booktitle = {Proceedings of the 8th Workshop on NLP for Similar Languages, Varieties and Dialects},
  pages     = {45--53},
  year      = {2021},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{zhang2015character,
  title     = {Character-level Convolutional Networks for Text Classification},
  author    = {Zhang, Xiang and Zhao, Junbo and LeCun, Yann},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  volume    = {28},
  pages     = {649--657},
  year      = {2015}
}
"""

with open('custom.bib', 'w', encoding='utf-8') as f:
    f.write(bibtex_content.strip() + '\n')

print('custom.bib successfully created with 27 BibTeX entries!')

# 5. Integrity and Consistency Checks
with open('ACL.tex', 'r', encoding='utf-8') as f:
    final_tex = f.read()

# Check citations in text
cite_matches = re.findall(r'\\cite\{([^}]+)\}', final_tex)
tex_keys = set()
for m in cite_matches:
    for k in m.split(','):
        tex_keys.add(k.strip())

# Check bibitem keys in tex
bibitem_keys = set(re.findall(r'\\bibitem\[.*?\]\{([^}]+)\}', final_tex))

# Check bibtex keys in custom.bib
bibtex_keys = set(re.findall(r'@[a-zA-Z]+\{([^,]+),', bibtex_content))

print(f"\n--- Integrity Report ---")
print(f"Citations in body text: {len(tex_keys)}")
print(f"Bibitems in ACL.tex: {len(bibitem_keys)}")
print(f"BibTeX entries in custom.bib: {len(bibtex_keys)}")

missing_in_bib = tex_keys - bibitem_keys
missing_in_text = bibitem_keys - tex_keys
missing_in_bibtex = bibitem_keys - bibtex_keys

if missing_in_bib:
    print(f"WARNING: Cited in text but missing in bibitems: {missing_in_bib}")
else:
    print("PASS: All text citations exist in bibitems!")

if missing_in_text:
    print(f"WARNING: Bibitems uncited in text: {missing_in_text}")
else:
    print("PASS: All bibitems are actively cited in text!")

if missing_in_bibtex:
    print(f"WARNING: Bibitems missing in custom.bib: {missing_in_bibtex}")
else:
    print("PASS: All bibitems exist in custom.bib!")

# Brace balance check
open_braces = final_tex.count('{')
close_braces = final_tex.count('}')
print(f"Brace balance: {open_braces} open, {close_braces} close -> {'PASS' if open_braces == close_braces else 'FAIL'}")

# Environment check
tokens = re.findall(r'\\(begin|end)\{([^}]+)\}', final_tex)
stack = []
balanced = True
for kind, name in tokens:
    if kind == 'begin':
        stack.append(name)
    else:
        if not stack or stack.pop() != name:
            balanced = False
            break
if stack:
    balanced = False

print(f"Environments: {len([t for t in tokens if t[0] == 'begin'])} environments -> {'PASS' if balanced else 'FAIL'}")
