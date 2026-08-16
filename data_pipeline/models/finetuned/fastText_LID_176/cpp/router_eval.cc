#include "src/fasttext.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// --------------------------------------------------
// Count characters in Sinhala Unicode block
// U+0D80 - U+0DFF
// --------------------------------------------------
double sinhalaScriptRatio(const std::string& text) {

    int sinhala = 0;
    int nonAscii = 0;

    for (size_t i = 0; i < text.size();) {

        unsigned char c = text[i];

        // ASCII
        if (c < 0x80) {
            i++;
            continue;
        }

        uint32_t codepoint = 0;
        size_t length = 0;

        if ((c & 0xE0) == 0xC0 && i + 1 < text.size()) {

            codepoint =
                ((c & 0x1F) << 6) |
                (text[i + 1] & 0x3F);

            length = 2;

        } else if ((c & 0xF0) == 0xE0 &&
                   i + 2 < text.size()) {

            codepoint =
                ((c & 0x0F) << 12) |
                ((text[i + 1] & 0x3F) << 6) |
                (text[i + 2] & 0x3F);

            length = 3;

        } else if ((c & 0xF8) == 0xF0 &&
                   i + 3 < text.size()) {

            codepoint =
                ((c & 0x07) << 18) |
                ((text[i + 1] & 0x3F) << 12) |
                ((text[i + 2] & 0x3F) << 6) |
                (text[i + 3] & 0x3F);

            length = 4;

        } else {

            i++;
            continue;
        }

        nonAscii++;

        if (codepoint >= 0x0D80 &&
            codepoint <= 0x0DFF) {

            sinhala++;
        }

        i += length;
    }

    if (nonAscii == 0) {
        return 0.0;
    }

    return static_cast<double>(sinhala)
           / nonAscii;
}

// --------------------------------------------------
// Original LID-176 prediction
// --------------------------------------------------
std::string predictBase(
    fasttext::FastText& model,
    const std::string& text) {

    std::istringstream input(text + "\n");

    std::vector<
        std::pair<fasttext::real, std::string>
    > predictions;

    bool ok = model.predictLine(
        input,
        predictions,
        1,
        0.0
    );

    if (!ok || predictions.empty()) {
        return "__label__unknown";
    }

    return predictions[0].second;
}


// --------------------------------------------------
// Convert specialist label → final label
// --------------------------------------------------
std::string specialistLabel(int prediction) {

    if (prediction == 0)
        return "__label__si";

    if (prediction == 1)
        return "__label__pli_sinh";

    return "__label__san_sinh";
}


// --------------------------------------------------
// Convert final target label to class number
// --------------------------------------------------
int targetIndex(const std::string& label) {

    if (label == "__label__si")
        return 0;

    if (label == "__label__pli_sinh")
        return 1;

    if (label == "__label__san_sinh")
        return 2;

    return -1;
}


int main() {

    fasttext::FastText model;

    model.loadModel(
        "../../data_pipeline/models/benchmark/fastText/lid.176.bin"
    );

    model.loadSpecialistHead(
        "specialist_head_balanced.bin"
    );

    std::ifstream file("mixed_eval.tsv");

    if (!file) {
        std::cerr << "Cannot open mixed_eval.tsv\n";
        return 1;
    }


    // -----------------------------------------------
    // Statistics
    // -----------------------------------------------

    long long oldTotal = 0;
    long long oldRouted = 0;
    long long oldChanged = 0;

    long long targetTotal = 0;
    long long targetRouted = 0;
    long long targetCorrect = 0;

    long long confusion[3][3] = {};
    long long otherPrediction[3] = {};
    long long actualCount[3] = {};

    std::ofstream routedOld(
        "routed_old_examples.tsv"
    );


    std::string line;

    while (std::getline(file, line)) {

        size_t p1 = line.find('\t');

        if (p1 == std::string::npos)
            continue;

        size_t p2 = line.find('\t', p1 + 1);

        if (p2 == std::string::npos)
            continue;

        size_t p3 = line.find('\t', p2 + 1);

        if (p3 == std::string::npos)
            continue;


        std::string kind =
            line.substr(0, p1);

        std::string label =
            line.substr(
                p1 + 1,
                p2 - p1 - 1
            );

        std::string source =
            line.substr(
                p2 + 1,
                p3 - p2 - 1
            );

        std::string text =
            line.substr(p3 + 1);


        bool useSpecialist =
            sinhalaScriptRatio(text) >= 0.5;


        // ===========================================
        // OLD LANGUAGES
        // ===========================================

        if (kind == "old") {

            oldTotal++;

            std::string original =
                predictBase(model, text);

            std::string routedPrediction =
                original;


            if (useSpecialist) {

                oldRouted++;

                int specialist =
                    model.predictSpecialist(text);

                routedPrediction =
                    specialistLabel(specialist);


                routedOld
                    << label << "\t"
                    << source << "\t"
                    << original << "\t"
                    << routedPrediction << "\t"
                    << text << "\n";
            }


            if (original != routedPrediction) {
                oldChanged++;
            }

            continue;
        }


        // ===========================================
        // TARGET LANGUAGES
        // ===========================================

        if (kind == "target") {

            int actual = std::stoi(label);

            if (actual < 0 || actual > 2)
                continue;

            targetTotal++;
            actualCount[actual]++;


            std::string finalPrediction;


            if (useSpecialist) {

                targetRouted++;

                int specialist =
                    model.predictSpecialist(text);

                finalPrediction =
                    specialistLabel(specialist);

            } else {

                // Router did not detect Sinhala script
                finalPrediction =
                    predictBase(model, text);
            }


            std::string expected =
                specialistLabel(actual);


            if (finalPrediction == expected) {
                targetCorrect++;
            }


            int predicted =
                targetIndex(finalPrediction);


            if (predicted >= 0) {

                confusion[actual][predicted]++;

            } else {

                otherPrediction[actual]++;
            }
        }
    }


    // ===============================================
    // RESULTS
    // ===============================================

    std::cout
        << std::fixed
        << std::setprecision(4);


    std::cout << "\n===== OLD LANGUAGE PRESERVATION =====\n\n";

    std::cout
        << "Old examples: "
        << oldTotal << "\n";

    std::cout
        << "Sent to specialist: "
        << oldRouted << "\n";

    std::cout
        << "Predictions changed: "
        << oldChanged << "\n";


    double preservation =
        oldTotal == 0
        ? 0.0
        : static_cast<double>(
              oldTotal - oldChanged
          ) / oldTotal;


    std::cout
        << "Prediction preservation rate: "
        << preservation
        << "\n";


    std::cout << "\n===== TARGET LANGUAGES =====\n\n";

    std::cout
        << "Target examples: "
        << targetTotal << "\n";

    std::cout
        << "Sent to specialist: "
        << targetRouted << "\n";


    double routingRecall =
        targetTotal == 0
        ? 0.0
        : static_cast<double>(
              targetRouted
          ) / targetTotal;


    std::cout
        << "Router coverage: "
        << routingRecall
        << "\n";


    double accuracy =
        targetTotal == 0
        ? 0.0
        : static_cast<double>(
              targetCorrect
          ) / targetTotal;


    std::cout
        << "Target accuracy: "
        << accuracy
        << "\n\n";


    const char* names[3] = {
        "Sinhala",
        "Pali",
        "Sanskrit"
    };


    double macroF1 = 0.0;


    for (int c = 0; c < 3; c++) {

        long long tp =
            confusion[c][c];

        long long fp = 0;

        for (int r = 0; r < 3; r++) {

            if (r != c) {
                fp += confusion[r][c];
            }
        }

        long long fn =
            actualCount[c] - tp;


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
            << names[c] << "\n"
            << "  Precision: "
            << precision << "\n"
            << "  Recall:    "
            << recall << "\n"
            << "  F1:        "
            << f1 << "\n\n";
    }


    macroF1 /= 3.0;

    std::cout
        << "Macro F1: "
        << macroF1
        << "\n";


    std::cout
        << "\nConfusion Matrix\n"
        << "Rows = Actual\n"
        << "Columns = Sinhala Pali Sanskrit Other\n\n";


    for (int i = 0; i < 3; i++) {

        std::cout
            << confusion[i][0] << "\t"
            << confusion[i][1] << "\t"
            << confusion[i][2] << "\t"
            << otherPrediction[i]
            << "\n";
    }


    std::cout
        << "\nOld examples routed to specialist saved to:\n"
        << "routed_old_examples.tsv\n";

    return 0;
}