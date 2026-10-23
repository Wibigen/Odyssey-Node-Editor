#pragma once
#include <cstdarg>
#include "lib.hpp"

// Debug output only (svcOutputDebugString): no socket, no network.
class Logger {
public:
    static void log(const char *fmt, ...);
    static void log(const char *fmt, va_list args);
};
