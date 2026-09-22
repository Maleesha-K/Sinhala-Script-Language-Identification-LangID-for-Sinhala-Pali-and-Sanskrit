// New code for this bundle; upstream fastText code is under native/fasttext/LICENSE.
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <numeric>
#include <sstream>
#include "fasttext.h"

namespace fasttext {
void Dictionary::appendLabelStable(const std::string& label) {
  if (getType(label) != entry_type::label)
    throw std::invalid_argument("Expected __label__ language tag");
  if (getId(label) >= 0) return;
  if (size_ + 1 >= int64_t(word2int_.size()) * 0.7) {
    word2int_.assign((size_ + 32) * 2, -1);
    for (int32_t i=0; i<size_; ++i) word2int_[find(words_[i].word)] = i;
  }
  entry e; e.word=label; e.count=1; e.type=entry_type::label;
  words_.push_back(e);
  word2int_[find(label)] = size_++;
  ++nlabels_;
}

void FastText::fineTune(const std::string& data, const std::string& labelsFile,
                        double lr, int64_t updates, int seed) {
  if (quant_ || args_->model != model_name::sup || args_->loss != loss_name::softmax)
    throw std::invalid_argument("This continuation backend requires a nonquantized supervised SOFTMAX .bin. It never silently converts hierarchical softmax.");
  if (updates < 0 || lr <= 0) throw std::invalid_argument("Invalid training budget/lr");
  std::ifstream lf(labelsFile);
  if (!lf) throw std::invalid_argument("Cannot read label file");
  const int oldLabels=dict_->nlabels();
  std::string s;
  while (std::getline(lf,s)) if (!s.empty()) dict_->appendLabelStable(s);
  if (dict_->nlabels()!=oldLabels) {
    auto old=std::dynamic_pointer_cast<DenseMatrix>(output_);
    auto next=std::make_shared<DenseMatrix>(dict_->nlabels(),args_->dim);
    next->zero(); // only newly appended rows are initialized
    for(int i=0;i<oldLabels;++i)
      for(int j=0;j<args_->dim;++j) next->at(i,j)=old->at(i,j);
    output_=next;
  }
  buildModel();
  std::cerr << "Retained " << oldLabels << " original labels; total "
            << dict_->nlabels() << "; input vocabulary/hash IDs unchanged.\n";
  if (updates==0) return;
  std::ifstream in(data);
  if (!in) throw std::invalid_argument("Cannot read training file");
  std::vector<std::string> lines;
  while(std::getline(in,s)) if(!s.empty()) lines.push_back(s);
  if(lines.empty()) throw std::invalid_argument("Empty training data");
  std::vector<size_t> order(lines.size());
  std::iota(order.begin(),order.end(),0);
  std::mt19937 rng(seed);
  Model::State state(args_->dim,output_->size(0),seed);
  std::vector<int32_t> features,targets;
  for(int64_t step=0;step<updates;++step) {
    size_t pos=step % order.size();
    if(pos==0) std::shuffle(order.begin(),order.end(),rng);
    std::istringstream row(lines[order[pos]]+"\n");
    dict_->getLine(row,features,targets);
    if(targets.size()!=1 || features.empty())
      throw std::invalid_argument("Every training row must have one known label and nonempty features");
    real rate=lr * (1.0 - double(step)/updates);
    supervised(state,rate,features,targets);
    if((step+1)%std::max<int64_t>(1,updates/20)==0)
      std::cerr << "Updates " << step+1 << "/" << updates << " loss=" << state.getLoss() << "\n";
  }
  wordVectors_.reset();
}
}

int main(int argc,char** argv) {
  try {
    if(argc<3) throw std::invalid_argument("Usage: lid_native inspect|predict|train|toy ...");
    std::string command=argv[1];
    fasttext::FastText model;
    if(command=="toy") {
      if(argc!=4) throw std::invalid_argument("toy DATA OUTPUT.bin");
      fasttext::Args a;
      a.input=argv[2];a.model=fasttext::model_name::sup;
      a.loss=fasttext::loss_name::softmax;a.dim=16;a.epoch=20;
      a.lr=0.5;a.thread=1;a.bucket=1000;a.minn=2;a.maxn=4;
      a.wordNgrams=2;a.minCount=1;a.verbose=0;
      model.train(a);model.saveModel(argv[3]);return 0;
    }
    model.loadModel(argv[2]);
    if(command=="inspect") {
      auto a=model.getArgs();auto d=model.getDictionary();
      std::cout << "loss\t" << a.lossToString(a.loss) << "\n";
      std::cout << "labels\t" << d->nlabels() << "\nwords\t" << d->nwords()
                << "\ndim\t" << a.dim << "\nbucket\t" << a.bucket << "\n";
      for(int i=0;i<d->nlabels();++i) std::cout << "label\t" << d->getLabel(i) << "\n";
    } else if(command=="train") {
      if(argc!=9) throw std::invalid_argument("train BASE DATA LABELS OUTPUT LR UPDATES SEED");
      model.fineTune(argv[3],argv[4],std::stod(argv[6]),std::stoll(argv[7]),std::stoi(argv[8]));
      model.saveModel(argv[5]);
    } else if(command=="predict") {
      if(argc!=5) throw std::invalid_argument("predict MODEL INPUT.txt OUTPUT.tsv");
      std::ifstream input(argv[3]);std::ofstream output(argv[4]);
      if(!input || !output) throw std::invalid_argument("Cannot open prediction files");
      std::string line;
      while(std::getline(input,line)) {
        std::istringstream row(line+"\n");
        std::vector<std::pair<fasttext::real,std::string>> pred;
        model.predictLine(row,pred,1,0.0);
        if(pred.empty()) output << "__EMPTY__\t0\n";
        else output << pred[0].second << "\t" << std::setprecision(9) << pred[0].first << "\n";
      }
    } else throw std::invalid_argument("Unknown command");
    return 0;
  } catch(const std::exception& e) {std::cerr << e.what() << "\n";return 1;}
}
