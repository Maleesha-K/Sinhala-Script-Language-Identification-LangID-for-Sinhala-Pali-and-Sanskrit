#include "src/fasttext.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

int main() {

    fasttext::FastText model;

    model.loadModel(
        "../../data_pipeline/models/benchmark/fastText/lid.176.bin"
    );

    model.loadSpecialistHead(
        "specialist_head_balanced.bin"
    );

    std::ifstream file("specialist_val_clean.tsv");

    if (!file) {
        std::cerr << "Cannot open specialist_val.tsv\n";
        return 1;
    }

    // rows = actual, columns = predicted
    long long confusion[3][3] = {};

    long long total = 0;
    long long correct = 0;

    std::string line;

    while (std::getline(file, line)) {

        size_t tab = line.find('\t');

        if (tab == std::string::npos) {
            continue;
        }

        int actual = std::stoi(
            line.substr(0, tab)
        );

        std::string text =
            line.substr(tab + 1);

        if (actual < 0 || actual > 2 ||
            text.empty()) {
            continue;
        }

        int predicted =
            model.predictSpecialist(text);

        confusion[actual][predicted]++;

        total++;

        if (actual == predicted) {
            correct++;
        }
    }

    const char* names[3] = {
        "Sinhala",
        "Pali",
        "Sanskrit"
    };

    std::cout << std::fixed
              << std::setprecision(4);

    double accuracy =
        static_cast<double>(correct) / total;

    std::cout
        << "\nAccuracy: "
        << accuracy
        << "\n\n";

    double macroF1 = 0.0;

    for (int c = 0; c < 3; c++) {

        long long tp = confusion[c][c];

        long long fp = 0;
        long long fn = 0;

        for (int i = 0; i < 3; i++) {

            if (i != c) {
                fp += confusion[i][c];
                fn += confusion[c][i];
            }
        }

        double precision =
            (tp + fp == 0)
            ? 0.0
            : static_cast<double>(tp)
              / (tp + fp);

        double recall =
            (tp + fn == 0)
            ? 0.0
            : static_cast<double>(tp)
              / (tp + fn);

        double f1 =
            (precision + recall == 0)
            ? 0.0
            : 2.0 * precision * recall
              / (precision + recall);

        macroF1 += f1;

        std::cout
            << names[c]
            << "\n";

        std::cout
            << "  Precision: "
            << precision
            << "\n";

        std::cout
            << "  Recall:    "
            << recall
            << "\n";

        std::cout
            << "  F1:        "
            << f1
            << "\n\n";
    }

    macroF1 /= 3.0;

    std::cout
        << "Macro F1: "
        << macroF1
        << "\n\n";

    std::cout
        << "Confusion Matrix\n";
    std::cout
        << "Rows = Actual, Columns = Predicted\n\n";

    for (int i = 0; i < 3; i++) {

        for (int j = 0; j < 3; j++) {

            std::cout
                << confusion[i][j]
                << "\t";
        }

        std::cout << "\n";
    }

    return 0;
}