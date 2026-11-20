#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
int main() {
    int i, ic = 0, cc = 0, oc = 0, j;
    char b[30], operators[30], identifiers[30];
    long constants[30];
    printf("enter the string : ");
    if (scanf("%29[^\n]", b) != 1) {
        return 1;
    }
    for (i = 0; b[i] != '\0'; i++) {
        if (isspace(static_cast<unsigned char>(b[i]))) {
            continue;
        } else if (isalpha(static_cast<unsigned char>(b[i]))) {
            identifiers[ic] = b[i];
            ic++;
        } else if (isdigit(static_cast<unsigned char>(b[i]))) {
            char *end;
            constants[cc++] = strtol(b + i, &end, 10);
            i = static_cast<int>(end - b) - 1;
        } else {
            if (b[i] == '*') {
                operators[oc] = '*';
                oc++;
            } else if (b[i] == '-') {
                operators[oc] = '-';
                oc++;
            } else if (b[i] == '+') {
                operators[oc] = '+';
                oc++;
            } else if (b[i] == '=') {
                operators[oc] = '=';
                oc++;
            }
        }
    }
    printf(" identifiers : ");
    for (j = 0; j < ic; j++) {
        printf("%c ", identifiers[j]);
    }
    printf("\n constants : ");
    for (j = 0; j < cc; j++) {
        printf("%ld ", constants[j]);
    }
    printf("\n operators : ");
    for (j = 0; j < oc; j++) {
        printf("%c ", operators[j]);
    }
}
