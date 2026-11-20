#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct three {
    char data[10], temp[7];
} s[30];
int main() {
    char d2[7];
    int i = 0, j = 1, len = 0;
    FILE *f1, *f2;

    f1 = fopen("sum.txt", "r");
    if (!f1) {
        perror("sum.txt");
        return 1;
    }
    while (len < 30 && fscanf(f1, "%9s", s[len].data) == 1) {
        len++;
    }
    fclose(f1);
    if (len < 5 || len % 2 == 0 || strcmp(s[1].data, "=") != 0) {
        return 1;
    }
    for (int k = 3; k < len; k += 2) {
        if (strcmp(s[k].data, "+") && strcmp(s[k].data, "-")) {
            return 1;
        }
    }
    f2 = fopen("out.txt", "w");
    if (!f2) {
        perror("out.txt");
        return 1;
    }
    snprintf(d2, sizeof d2, "t%d", j);
    strcpy(s[j].temp, d2);
    if (!strcmp(s[3].data, "+")) {
        fprintf(f2, "%s=%s+%s", s[j].temp, s[i + 2].data, s[i + 4].data);
        j++;
    } else if (!strcmp(s[3].data, "-")) {
        fprintf(f2, "%s=%s-%s", s[j].temp, s[i + 2].data, s[i + 4].data);
        j++;
    }
    for (i = 4; i < len - 2; i += 2) {
        snprintf(d2, sizeof d2, "t%d", j);
        strcpy(s[j].temp, d2);
        if (!strcmp(s[i + 1].data, "+")) {
            fprintf(f2, "\n%s=%s+%s", s[j].temp, s[j - 1].temp, s[i + 2].data);
        } else if (!strcmp(s[i + 1].data, "-")) {
            fprintf(f2, "\n%s=%s-%s", s[j].temp, s[j - 1].temp, s[i + 2].data);
        }
        j++;
    }
    fprintf(f2, "\n%s=%s", s[0].data, s[j - 1].temp);
    fclose(f2);
}
