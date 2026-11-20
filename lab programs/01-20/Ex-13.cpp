#include <iostream>
#include <string>

int main() {
    std::cout << "The grammar is: S->aS, S->Sb, S->ab\n"
                 "Enter the string to be checked:\n";
    std::string input;
    if (!std::getline(std::cin, input)) {
        return 1;
    }

    // The grammar produces one or more a's followed by one or more b's.
    const auto firstB = input.find_first_not_of('a');
    const bool accepted = firstB != std::string::npos && firstB > 0 &&
                          input.find_first_not_of('b', firstB) == std::string::npos;
    std::cout << (accepted ? "String accepted\n"
                           : "The string does not belong to the specified grammar\n");
}
