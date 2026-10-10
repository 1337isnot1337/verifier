/* Trusted adapter: serialize Lake targets without an extra script interpreter. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <time.h>
#ifndef REAL_LAKE
#error REAL_LAKE is required
#endif
#ifndef CONTROL
#error CONTROL is required
#endif
#ifndef SOLUTION_MODULE
#error SOLUTION_MODULE is required
#endif
int main(int argc, char **argv) {
    if (setenv("LEAN_NUM_THREADS", "4", 1)) return 1;
    if (argc != 3 || strcmp(argv[1], "build") || strcmp(argv[2], SOLUTION_MODULE)) {
        argv[0] = REAL_LAKE;
        execv(REAL_LAKE, argv);
        perror("execv lake"); return 1;
    }
    FILE *f = fopen(CONTROL "/chain-targets.txt", "r");
    if (!f) { perror("chain targets"); return 1; }
    char *line = NULL; size_t cap = 0; unsigned int index = 0;
    while (getline(&line, &cap, f) >= 0) {
        line[strcspn(line, "\r\n")] = 0;
        if (!line[0]) continue;
        struct timespec start, end;
        clock_gettime(CLOCK_MONOTONIC, &start);
        printf("VERIFIER source chain %u: %s\n", index, line); fflush(stdout);
        pid_t child = fork();
        if (child < 0) { perror("fork"); return 1; }
        if (child == 0) {
            char *args[] = { REAL_LAKE, "build", line, NULL };
            execv(REAL_LAKE, args); perror("execv lake"); _exit(127);
        }
        int status;
        if (waitpid(child, &status, 0) < 0) { perror("waitpid"); return 1; }
        int code = WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
        clock_gettime(CLOCK_MONOTONIC, &end);
        double secs = end.tv_sec - start.tv_sec + (end.tv_nsec - start.tv_nsec) / 1e9;
        printf("VERIFIER source chain %u: exit=%d seconds=%.3f\n", index++, code, secs);
        fflush(stdout);
        if (code) return code;
    }
    free(line); fclose(f); return 0;
}
