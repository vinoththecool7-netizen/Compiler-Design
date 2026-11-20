#include <iostream>
#include <string>

void showStep(const std::string &stack, const std::string &remaining, const std::string &action) {
    std::cout << '$' << stack << "\t\t" << remaining << "$\t\t" << action << '\n';
}

int main() {
    std::cout << "SHIFT REDUCE PARSER\n"
                 "E->E+E | E/E | E*E | a | b\n"
                 "Enter the input symbols: ";
    std::string input;
    if (!std::getline(std::cin, input)) {
        return 1;
    }

    std::string stack;
    std::cout << "Stack\t\tInput\t\tAction\n";
    showStep(stack, input, "--");
    for (std::size_t index = 0; index < input.size(); ++index) {
        const char token = input[index];
        const std::string remaining = input.substr(index + 1);
        if (std::string("aAbB+/*").find(token) == std::string::npos) {
            showStep(stack, remaining, "REJECT");
            return 0;
        }
        stack += token;
        showStep(stack, remaining, std::string("Shift ") + token);

        if (token == 'a' || token == 'b' || token == 'A' || token == 'B') {
            stack.back() = 'E';
            showStep(stack, remaining, std::string("E->") + token);
        }

        const auto size = stack.size();
        if (size >= 3 && stack[size - 3] == 'E' && stack.back() == 'E' &&
            std::string("+/*").find(stack[size - 2]) != std::string::npos) {
            const std::string handle = stack.substr(size - 3);
            stack.resize(size - 2);
            showStep(stack, remaining, "E->" + handle);
        }
    }

    showStep(stack, "", stack == "E" ? "ACCEPT" : "REJECT");
}
