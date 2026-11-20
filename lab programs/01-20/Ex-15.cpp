#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *input;
int i = 0;

char lasthandle[6];
char stack[50];
const char *handles[] = {")E(", "E*E", "E/E", "E+E", "E-E", "i", "E^E"};

int top = 0, l;

char prec[9][9] = {
    {'>', '>', '<', '<', '<', '<', '<', '>', '>'}, {'>', '>', '<', '<', '<', '<', '<', '>', '>'},
    {'>', '>', '>', '>', '<', '<', '<', '>', '>'}, {'>', '>', '>', '>', '<', '<', '<', '>', '>'},
    {'>', '>', '>', '>', '<', '<', '<', '>', '>'}, {'>', '>', '>', '>', '>', 'e', 'e', '>', '>'},
    {'<', '<', '<', '<', '<', '<', '<', '>', 'e'}, {'>', '>', '>', '>', '>', 'e', 'e', '>', '>'},
    {'<', '<', '<', '<', '<', '<', '<', '<', '>'}};

int getindex(char c) {
    switch (c) {
    case '+':
        return 0;
    case '-':
        return 1;
    case '*':
        return 2;
    case '/':
        return 3;
    case '^':
        return 4;
    case 'i':
        return 5;
    case '(':
        return 6;
    case ')':
        return 7;
    case '$':
        return 8;
    }
    return -1;
}

void shift() {
    stack[++top] = input[i++];
    stack[top + 1] = '\0';
}

int reduce() {
    int k, len, t, found;

    for (k = 0; k < static_cast<int>(sizeof handles / sizeof handles[0]); k++) {
        len = strlen(handles[k]);

        if (top + 1 >= len) {
            found = 1;

            for (t = 0; t < len; t++) {
                if (stack[top - t] != handles[k][t]) {
                    found = 0;
                    break;
                }
            }

            if (found) {
                stack[top - len + 1] = 'E';
                top = top - len + 1;

                strcpy(lasthandle, handles[k]);
                stack[top + 1] = '\0';

                return 1;
            }
        }
    }

    return 0;
}

void dispstack() {
    int j;

    for (j = 0; j <= top; j++) {
        printf("%c", stack[j]);
    }
}

void dispinput() {
    int j;

    for (j = i; j < l; j++) {
        printf("%c", input[j]);
    }
}

int main() {
    input = (char *)malloc(50 * sizeof(char));

    printf("\nEnter the string\n");
    if (!input || scanf("%47s", input) != 1) {
        free(input);
        return 1;
    }

    strcat(input, "$");
    l = strlen(input);

    strcpy(stack, "$");
    top = 0;

    printf("\nSTACK\tINPUT\tACTION");

    while (i < l) {
        shift();

        printf("\n");
        dispstack();
        printf("\t");
        dispinput();
        printf("\tShift");

        if (i < l) {
            const int right = getindex(input[i]);
            if (right < 0) {
                break;
            }

            for (;;) {
                int terminal = top;
                while (stack[terminal] == 'E') {
                    terminal--;
                }
                const int left = getindex(stack[terminal]);
                if (left < 0 || prec[left][right] != '>' || !reduce()) {
                    break;
                }

                printf("\n");
                dispstack();
                printf("\t");
                dispinput();
                printf("\tReduced: E->%s", lasthandle);
            }
        }
    }

    while (reduce()) {
        printf("\n");
        dispstack();
        printf("\t");
        dispinput();
        printf("\tReduced: E->%s", lasthandle);
    }

    if (i == l && strcmp(stack, "$E$") == 0) {
        printf("\nAccepted;");
    } else {
        printf("\nNot Accepted;");
    }

    free(input);

    return 0;
}
