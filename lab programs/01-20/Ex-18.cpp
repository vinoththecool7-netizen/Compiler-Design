#include <stdio.h>
#include <string.h>
int main() {
    int n, i, j;
    char a[50][50];
    printf("enter the no: intermediate code:");
    if (scanf("%d", &n) != 1 || n < 1 || n > 50) {
        return 1;
    }
    for (i = 0; i < n; i++) {
        printf("enter the 3 address code:%d:", i + 1);
        for (j = 0; j < 5; j++) {
            if (scanf(" %c", &a[i][j]) != 1) {
                return 1;
            }
        }
    }
    printf("the generated code is:");
    for (i = 0; i < n; i++) {
        printf("\n mov %c,R%d", a[i][2], i);
        if (a[i][3] == '-') {
            printf("\n sub %c,R%d", a[i][4], i);
        }
        if (a[i][3] == '+') {
            printf("\n add %c,R%d", a[i][4], i);
        }
        if (a[i][3] == '*') {
            printf("\n mul %c,R%d", a[i][4], i);
        }
        if (a[i][3] == '/') {
            printf("\n div %c,R%d", a[i][4], i);
        }
        printf("\n mov R%d,%c", i, a[i][0]);
        printf("\n");
    }
    return 0;
}
