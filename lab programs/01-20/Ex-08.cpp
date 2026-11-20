#include <ctype.h>
#include <stdio.h>
#include <string.h>
int limit, x = 0;
bool following[256], findingFirst[256];
char production[10][10], array[10];

void find_first(char ch);
void find_follow(char ch);
void Array_Manipulation(char ch);

int main() {
    int count;
    char option, ch;
    printf("\nEnter Total Number of Productions:\t");
    if (scanf("%d", &limit) != 1 || limit < 1 || limit > 10) {
        return 1;
    }
    for (count = 0; count < limit; count++) {
        printf("\nValue of Production Number [%d]:\t", count + 1);
        if (scanf("%9s", production[count]) != 1) {
            return 1;
        }
    }
    do {
        x = 0;
        printf("\nEnter production Value to Find Follow:\t");
        if (scanf(" %c", &ch) != 1) {
            return 0;
        }
        find_follow(ch);
        printf("\nFollow Value of %c:\t{ ", ch);
        for (count = 0; count < x; count++) {
            printf("%c ", array[count]);
        }
        printf("}\n");
        printf("To Continue, Press Y:\t");
        if (scanf(" %c", &option) != 1) {
            return 0;
        }
    } while (option == 'y' || option == 'Y');
    return 0;
}

void find_follow(char ch) {
    int i, j;
    const unsigned char symbol = ch;
    if (following[symbol]) {
        return;
    }
    following[symbol] = true;
    if (production[0][0] == ch) {
        Array_Manipulation('$');
    }
    for (i = 0; i < limit; i++) {
        for (j = 2; production[i][j] != '\0'; j++) {
            if (production[i][j] == ch) {
                if (production[i][j + 1] != '\0') {
                    find_first(production[i][j + 1]);
                }
                if (production[i][j + 1] == '\0' && ch != production[i][0]) {
                    find_follow(production[i][0]);
                }
            }
        }
    }
    following[symbol] = false;
}

void find_first(char ch) {
    int k;
    const unsigned char symbol = ch;
    if (findingFirst[symbol]) {
        return;
    }
    findingFirst[symbol] = true;
    if (!(isupper(ch))) {
        Array_Manipulation(ch);
    }
    for (k = 0; k < limit; k++) {
        if (production[k][0] == ch) {
            if (production[k][2] == '$') {
                find_follow(production[k][0]);
            } else if (islower(production[k][2])) {
                Array_Manipulation(production[k][2]);
            } else {
                find_first(production[k][2]);
            }
        }
    }
    findingFirst[symbol] = false;
}

void Array_Manipulation(char ch) {
    int count;
    for (count = 0; count < x; count++) {
        if (array[count] == ch) {
            return;
        }
    }
    if (x < static_cast<int>(sizeof array)) {
        array[x++] = ch;
    }
}
