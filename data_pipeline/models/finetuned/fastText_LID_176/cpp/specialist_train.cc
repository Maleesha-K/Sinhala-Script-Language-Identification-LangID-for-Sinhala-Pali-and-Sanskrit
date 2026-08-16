#include "src/fasttext.h"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

struct Example {
    int label;
    std::string text;
};

int main() {

    // -------------------------
    // Load training data
    // -------------------------

    std::ifstream file("specialist_train_clean.tsv");

    if (!file) {
        std::cerr << "Cannot open specialist_train.tsv\n";
        return 1;
    }

    std::vector<Example> examples;

    std::string line;

    while (std::getline(file, line)) {

        size_t tab = line.find('\t');

        if (tab == std::string::npos) {
            continue;
        }

        int label = std::stoi(
            line.substr(0, tab)
        );

        std::string text =
            line.substr(tab + 1);

        if (label < 0 || label > 2) {
            continue;
        }

        if (text.empty()) {
            continue;
        }

        examples.push_back({
            label,
            text
        });
    }

    std::cout
        << "Loaded "
        << examples.size()
        << " examples\n";



        long long classCounts[3] = {0, 0, 0};

for (const auto& ex : examples) {
    classCounts[ex.label]++;
}

float classWeights[3];

for (int c = 0; c < 3; c++) {

    classWeights[c] =
        static_cast<float>(examples.size())
        / (3.0f * classCounts[c]);

    std::cout
        << "Class " << c
        << " count = " << classCounts[c]
        << ", weight = " << classWeights[c]
        << "\n";
}
    // -------------------------
    // Load original LID-176
    // -------------------------

    fasttext::FastText model;

    model.loadModel(
        "../../data_pipeline/models/benchmark/fastText/lid.176.bin"
    );

    // Create the new specialist classifier
    model.initializeSpecialistHead();


    // -------------------------
    // Training configuration
    // -------------------------

    const int epochs = 5;

    const float startLR = 0.05;
    const float endLR   = 0.005;

    std::mt19937 rng(42);

    long long totalSteps =
        static_cast<long long>(epochs)
        * examples.size();

    long long currentStep = 0;


    // -------------------------
    // Train
    // -------------------------

    for (int epoch = 0;
         epoch < epochs;
         epoch++) {

        std::shuffle(
            examples.begin(),
            examples.end(),
            rng
        );

        for (const auto& ex : examples) {

            float progress =
                static_cast<float>(currentStep)
                / totalSteps;

            float lr =
                startLR
                + (endLR - startLR)
                * progress;

            model.trainSpecialistExample(
    ex.text,
    ex.label,
    lr,
    classWeights[ex.label]
);

            currentStep++;
        }

        std::cout
            << "Epoch "
            << (epoch + 1)
            << "/"
            << epochs
            << " completed\n";
    }


    // -------------------------
    // Save specialist head
    // -------------------------

    model.saveSpecialistHead(
        "specialist_head_balanced_clean.bin"
    );

    std::cout
        << "\nTraining complete.\n";

    std::cout
        << "Saved: specialist_head.bin\n";

    return 0;
}