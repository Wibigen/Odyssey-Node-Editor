#include "Logger.hpp"
#include <cstdio>
#include <cstring>

static void out(const char *buf) {
    unsigned long len = strlen(buf);
    // svcOutputDebugString(buf, len): the registers are set inside the asm block, so nothing can clobber them in between
    // (v7.3 used "register ... asm(x0)" variables and a strlen() call in between: strlen got a wrong pointer and the game crashed)
    asm volatile("mov x0, %0\n\tmov x1, %1\n\tsvc 0x27"
                 :
                 : "r"(buf), "r"(len)
                 : "x0", "x1", "memory");
}

void Logger::log(const char *fmt, va_list args) {
    char buffer[0x500];
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    out(buffer);
}

void Logger::log(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    log(fmt, args);
    va_end(args);
}
