#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>

int isKeyword(const char buffer[]) {
    char keywords[32][10] = {
        "main",   "auto",   "break",  "case",     "char",     "const", "continue", "default",
        "do",     "double", "else",   "enum",     "extern",   "float", "for",      "goto",
        "if",     "int",    "long",   "register", "return",   "short", "signed",   "sizeof",
        "static", "struct", "switch", "typedef",  "unsigned", "void",  "printf",   "while"};
    int i, flag = 0;
    for (i = 0; i < 32; ++i) {
        if (strcmp(keywords[i], buffer) == 0) {
            flag = 1;
            break;
        }
    }
    return flag;
}

int main() {
    int ch;
    std::string buffer;
    const char operators[] = "+-*/%=";
    FILE *fp;
    int i;
    fp = fopen("flex_input.txt", "r");
    if (fp == NULL) {
        printf("error while opening the file\n");
        exit(0);
    }
    while ((ch = fgetc(fp)) != EOF) {
        for (i = 0; i < 6; ++i) {
            if (ch == operators[i]) {
                printf("%c is operator\n", ch);
            }
        }

        if (isalnum(ch) || ch == '_') {
            buffer += static_cast<char>(ch);
        } else if (!buffer.empty()) {
            printf("%s is %s\n", buffer.c_str(),
                   isKeyword(buffer.c_str()) ? "keyword" : "identifier");
            buffer.clear();
        }
    }
    if (!buffer.empty()) {
        printf("%s is %s\n", buffer.c_str(), isKeyword(buffer.c_str()) ? "keyword" : "identifier");
    }
    fclose(fp);
    return 0;
}
