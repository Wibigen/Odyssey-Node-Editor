#pragma once

#include "lib.hpp"
// do { } while (0): works inside "if (x) IM_ASSERT(..); else ..."
#define IM_ASSERT(_EXPR) do { if (!(_EXPR)) { __builtin_trap(); } } while (0)