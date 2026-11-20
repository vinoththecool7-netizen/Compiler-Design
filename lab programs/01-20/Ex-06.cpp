#include <ctype.h>
#include <stdio.h>
#include <string.h>
int main() {
    char a[10];
    int i = 1;
    printf("\n Enter an identifier:");
    if (!fgets(a, sizeof a, stdin)) {
        return 1;
    }
    a[strcspn(a, "\n")] = '\0';
    bool valid = isalpha(static_cast<unsigned char>(a[0]));
    while (valid && a[i] != '\0') {
        valid = isalnum(static_cast<unsigned char>(a[i]));
        i++;
    }
    printf(valid ? "\n Valid identifier" : "\n Not a valid identifier");
}
