#include <iostream>
#include <string>

int main() {
    std::cout << "Enter Production : S->";
    std::string grammar;
    if (!std::getline(std::cin, grammar)) {
        return 1;
    }

    const auto separator = grammar.find('|');
    if (separator == std::string::npos || grammar.find('|', separator + 1) != std::string::npos) {
        std::cout << "Enter two alternatives separated by |.\n";
        return 1;
    }

    const std::string first = grammar.substr(0, separator);
    const std::string second = grammar.substr(separator + 1);
    std::size_t prefix = 0;
    while (prefix < first.size() && prefix < second.size() && first[prefix] == second[prefix]) {
        ++prefix;
    }

    if (prefix == 0) {
        std::cout << "No common prefix.\n";
        return 0;
    }

    std::cout << "S->" << first.substr(0, prefix) << "X\n"
              << "X->" << (prefix == first.size() ? "ε" : first.substr(prefix)) << '|'
              << (prefix == second.size() ? "ε" : second.substr(prefix)) << '\n';
}
