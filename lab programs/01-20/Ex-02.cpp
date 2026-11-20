#include <stdio.h>
#include <string.h>
int main() {
    char com[30];

    printf("\n Enter comment:");
    if (!fgets(com, sizeof com, stdin)) {
        return 1;
    }
    com[strcspn(com, "\n")] = '\0';
    if (com[0] == '/') {
        if (com[1] == '/') {
            printf("\n It is a comment");
        } else if (com[1] == '*') {
            printf(strstr(com + 2, "*/") ? "\n It is a comment" : "\n It is not a comment");
        } else {
            printf("\n It is not a comment");
        }
    } else {
        printf("\n It is not a comment");
    }
}
