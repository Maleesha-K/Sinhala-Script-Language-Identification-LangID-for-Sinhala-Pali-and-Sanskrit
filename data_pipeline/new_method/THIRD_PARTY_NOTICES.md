# Third-party code and checkpoints

`native/fasttext/src/` is fastText v0.9.2 from Facebook, Inc., under the MIT license in `native/fasttext/LICENSE`. Two declarations were added to `dictionary.h` and `fasttext.h`; their implementations are in `native/continue.cc`. The compiler includes `cstdint` explicitly for compatibility with recent GCC releases. The original training, feature extraction, and serialization implementations are retained.

`lidlab/backends.py` contains an independent trainable implementation of the released ConLID mean/sum pooling architecture. It loads upstream tensors, vocabulary, config, and labels. The large model files are downloaded at runtime and are not part of this ZIP.

Model and dataset licenses are independent of this source package. Meta's model card specifies CC-BY-NC-4.0 for lid218e. GlotLID's current model card specifies Apache-2.0 plus notices. Check the ConLID release's terms before redistributing fine-tuned weights; this package does not assign a new license to those weights. Retain upstream attribution and notices in any model you publish. No model upload or publication is performed automatically.
